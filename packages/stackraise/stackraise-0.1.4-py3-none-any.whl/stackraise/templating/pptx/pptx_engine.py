import re
from typing import Optional, Union
from pathlib import Path
from io import BytesIO

from pptx import Presentation
from pptx.slide import Slide
from pydantic import BaseModel

from ..parser import create_jinja_env, evaluate_condition, evaluate_conditional_block, extract_slide_conditional_block, extract_slide_loop
from .slide_renderer import render_slide
from ..tracer import Tracer
from ..exceptions import TemplateNotFoundError, RenderError
from copy import deepcopy

"""
TODO: Implementar soporte para variables de tipo 'of' en los bucles de Jinja2.
    Este operador permite iterar sobre listas y para cada elemento generar
    un slide duplicado con el contexto actualizado.
"""


class PptxTemplateEngine:

    @staticmethod
    def _resolve_path(ctx: dict, path: str):
        """
        Resuelve rutas 'a.b.c' en dicts/objetos simples.
        """
        cur = ctx
        for part in [p.strip() for p in path.split('.') if p.strip()]:
            if isinstance(cur, dict):
                cur = cur.get(part, None)
            else:
                cur = getattr(cur, part, None)
            if cur is None:
                return None
        return cur

    @staticmethod
    def render_from_template(
        context: BaseModel,
        template_path: str,
        output_path: Optional[str] = None
    ) -> Union[str, BytesIO]:
        tracer = Tracer()
        tracer.start()

        template_file = Path(template_path)
        if not template_file.exists():
            raise TemplateNotFoundError(f"Plantilla no encontrada en ruta: {template_path}")

        try:
            prs = Presentation(template_path)
            # serializar el model pero RESTAURAR objetos ImageData top-level
            context_dict = context.model_dump(by_alias=False, mode="python")
            try:
                # import tardío para evitar ciclos
                from stackraise.templating.image.model import ImageData
            except Exception:
                ImageData = None

            if ImageData is not None:
                # Restaurar campos top-level que en el BaseModel son instancias ImageData
                for name, raw_value in context.__dict__.items():
                   if isinstance(raw_value, ImageData):
                        context_dict[name] = raw_value
                        
            jinja_env = create_jinja_env()

            slides = list(prs.slides)
            slides_to_remove = []

            for idx, slide in enumerate(slides):
                loop_found = False
                slide_level_conditional_found = False

                # Buscar en todas las formas de texto de la slide
                slide_text = ""
                for shape in slide.shapes:
                    if shape.has_text_frame:
                        slide_text += shape.text_frame.text + " "

                # Primero verificar si hay un bucle A NIVEL DE SLIDE
                loop_info = extract_slide_loop(slide_text)
                if loop_info:
                    loop_var, loop_list, loop_type = loop_info
                    loop_found = True

                    #items = context_dict.get(loop_list, []) or []
                    items = PptxTemplateEngine._resolve_path(context_dict, loop_list) or []

                    # if loop_type == "of":
                    #     tracer.log_slide_duplication(idx, len(items))
                    #     for i, item in enumerate(items):
                    #         new_slide = PptxTemplateEngine._duplicate_slide(prs, slide)
                    #         local_context = context_dict.copy()
                    #         local_context[loop_var] = item
                    #         render_slide(new_slide, local_context, jinja_env, tracer)

                    #     slides_to_remove.append(slide)
                    # else:
                    #     render_slide(slide, context_dict, jinja_env, tracer)
                    if loop_type == "of":
                        tracer.log_duplication(idx, len(items), "slide")
                        for i, item in enumerate(items):
                            new_slide = PptxTemplateEngine._duplicate_slide(prs, slide)
                            local_context = context_dict.copy()
                            local_context[loop_var] = item
                            # Evita que Jinja procese el 'for of' en la duplicada
                            PptxTemplateEngine._unwrap_slide_for_blocks(new_slide)
                            render_slide(new_slide, local_context, jinja_env, tracer)

                        slides_to_remove.append(slide)
                    else:
                        render_slide(slide, context_dict, jinja_env, tracer)

                # Si no hay bucle, verificar si hay condicional A NIVEL DE SLIDE
                elif not loop_found:
                    conditional_info = extract_slide_conditional_block(slide_text)
                    if conditional_info:
                        slide_level_conditional_found = True
                        try:
                            if conditional_info['has_block_structure']:
                                # Bloque condicional completo con if/elif/else
                                condition_result = evaluate_conditional_block(slide_text, context_dict, jinja_env)
                                tracer.log_conditional(idx, f"bloque condicional a nivel slide", condition_result)
                            else:
                                # Condicional simple
                                condition = conditional_info['condition']
                                condition_result = evaluate_condition(condition, context_dict, jinja_env)
                                tracer.log_conditional(idx, condition, condition_result)
                            
                            if condition_result:
                                # Condición verdadera: renderizar la slide
                                render_slide(slide, context_dict, jinja_env, tracer)
                            else:
                                # Condición falsa: marcar slide para eliminación
                                slides_to_remove.append(slide)
                                
                        except Exception as e:
                            tracer.log_error(f"Error evaluando condición en slide {idx}: {e}")
                            # En caso de error, mantener la slide pero sin renderizar
                            render_slide(slide, context_dict, jinja_env, tracer)

                # Si no hay ni bucle ni condicional A NIVEL DE SLIDE, renderizar normalmente
                # (los condicionales a nivel de texto se manejan en render_slide)
                if not loop_found and not slide_level_conditional_found:
                    render_slide(slide, context_dict, jinja_env, tracer)

            # Remover slides marcadas para eliminación
            for slide in slides_to_remove:
                PptxTemplateEngine._remove_slide(prs, slide)

            if output_path:
                prs.save(output_path)
                tracer.end()
                return str(output_path)
            else:
                pptx_io = BytesIO()
                prs.save(pptx_io)
                pptx_io.seek(0)
                tracer.end()
                return pptx_io

        except Exception as e:
            tracer.log_error(f"Error en render_from_template: {e}")
            raise RenderError(f"Fallo al renderizar plantilla PPTX: {e}")

    @staticmethod
    def _duplicate_slide(prs: Presentation, slide: Slide) -> Slide:
        new_slide = prs.slides.add_slide(slide.slide_layout)
        for shape in slide.shapes:
            el = shape.element
            new_el = deepcopy(el)
            new_slide.shapes._spTree.insert_element_before(new_el, 'p:extLst')
        return new_slide

    @staticmethod
    def _remove_slide(prs: Presentation, slide: Slide):
        slide_id = slide.slide_id
        slides = prs.slides._sldIdLst
        for sld in slides:
            if sld.get("id") == str(slide_id):
                slides.remove(sld)
                break

    @staticmethod
    def _unwrap_slide_for_blocks(slide: Slide) -> None:
        """Quita etiquetas {% for ... %}/{% endfor %} in-place sin tocar formato."""
        start_tag = re.compile(r"""{%\s*for\s+\w+\s+(?:of|in)\s+.+?\s*%}""")
        end_tag = re.compile(r"""{%\s*endfor\s*%}""")
        for shape in slide.shapes:
            if not getattr(shape, "has_text_frame", False):
                continue
            tf = shape.text_frame
            for p in tf.paragraphs:
                for r in p.runs:
                    if not r.text:
                        continue
                    # Elimina sólo las etiquetas, deja el cuerpo intacto
                    txt = start_tag.sub("", r.text)
                    txt = end_tag.sub("", txt)
                    r.text = txt