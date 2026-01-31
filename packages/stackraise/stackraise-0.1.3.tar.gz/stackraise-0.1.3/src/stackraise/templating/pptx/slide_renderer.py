from pptx.slide import Slide
from pptx.shapes.base import BaseShape
from pptx.dml.color import RGBColor
from stackraise.templating.image.processor import ImageProcessor
from ..parser import has_image_variables, render_text
from ..tracer import Tracer
import re

def remove_for_of_blocks(text: str) -> str:
    # Desenrolla bucles a nivel de slide: conserva solo el cuerpo
    #pattern = r"""{%\s*for\s+\w+\s+(?:of|in)\s+\w+\s*%}(.*?){%\s*endfor\s*%}"""
    pattern = r"""{%\s*for\s+\w+\s+(?:of|in)\s+.+?\s*%}(.*?){%\s*endfor\s*%}"""
    return re.sub(pattern, r"\1", text, flags=re.DOTALL)

def has_conditional_blocks(text: str) -> bool:
    """
    Verifica si el texto contiene bloques condicionales.
    """
    pattern = r"""{%\s*if\s+.+?\s*%}"""
    return bool(re.search(pattern, text))

def has_text_level_loops(text: str) -> bool:
    """
    Verifica si el texto contiene bucles que deben procesarse como texto
    (no como duplicación de slides).
    """
    # Buscar bucles que estén mezclados con otro contenido
    lines = text.strip().split('\n')
    has_loop = False
    has_other_content = False
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        #if re.search(r'{%\s*for\s+\w+\s+(of|in)\s+\w+\s*%}', line):
        if re.search(r'{%\s*for\s+\w+\s+(?:of|in)\s+.+?\s*%}', line):
            has_loop = True
        #elif not re.search(r'{%\s*(for|endfor|if|elif|else|endif)\s*.*%}', line):
        elif not re.search(r'{%\s*(for|endfor|if|elif|else|endif)\s*.*%}', line):
            has_other_content = True
    
    return has_loop and has_other_content


def _copy_run_font(dst_run, src_run):
    try:
        dst_font = dst_run.font
        src_font = src_run.font
        dst_font.name = src_font.name
        dst_font.size = src_font.size
        dst_font.bold = src_font.bold
        dst_font.italic = src_font.italic
        dst_font.underline = src_font.underline
        # Color: intenta RGB si existe
        try:
            rgb = src_font.color.rgb
            if rgb is not None:
                dst_font.color.rgb = RGBColor(rgb[0], rgb[1], rgb[2]) if isinstance(rgb, tuple) else rgb
        except Exception:
            try:
                dst_font.color.theme_color = src_font.color.theme_color
            except Exception:
                pass
    except Exception:
        pass

def _snapshot_base_style(text_frame):
    base_para = text_frame.paragraphs[0] if text_frame.paragraphs else None
    base_run = base_para.runs[0] if (base_para and base_para.runs) else None
    return base_para, base_run

def write_text_preserving_formatting(text_frame, text: str):
    # Captura estilo base antes de limpiar
    base_para_before, base_run_before = _snapshot_base_style(text_frame)

    # Limpia el contenido (deja un párrafo vacío)
    try:
        text_frame.clear()
    except Exception:
        pass

    lines = (text or "").splitlines() or [""]
    for idx, line in enumerate(lines):
        para = text_frame.paragraphs[0] if idx == 0 else text_frame.add_paragraph()

        # Restituye nivel/alineación del párrafo base si existe
        try:
            if base_para_before is not None:
                para.level = base_para_before.level
                para.alignment = base_para_before.alignment
        except Exception:
            pass

        run = para.runs[0] if para.runs else para.add_run()
        # Copia estilo del run base si existe
        if base_run_before is not None:
            _copy_run_font(run, base_run_before)
        run.text = line


def has_only_simple_variables(text: str) -> bool:
    # Hay variables {{ ... }} pero no bloques {% ... %}
    return ("{{" in text) and ("{%" not in text)

def render_runs_preserving_formatting(text_frame, context: dict, jinja_env):
    # Sustituye {{ expr }} dentro de cada run conservando su formato
    var_re = re.compile(r"\{\{\s*(.*?)\s*\}\}")
    for paragraph in text_frame.paragraphs:
        for run in paragraph.runs:
            original = run.text or ""
            if not original:
                continue
            def repl(m: re.Match) -> str:
                expr = m.group(1)
                try:
                    tpl = jinja_env.from_string("{{ " + expr + " }}")
                    return str(tpl.render(context))
                except Exception:
                    # Si falla, deja el placeholder intacto
                    return m.group(0)
            replaced = var_re.sub(repl, original)
            run.text = replaced

def render_slide(slide: Slide, context: dict, jinja_env, tracer: Tracer):
    # Primero procesar imágenes (variables ImageData)
    ImageProcessor.process_slide_images(slide, context, tracer)
    
    # Luego procesar texto normal
    for shape in slide.shapes:
        if not getattr(shape, "has_text_frame", False):
            continue

        text_frame = shape.text_frame
        all_text = ""
        for paragraph in text_frame.paragraphs:
            all_text += "".join(run.text for run in paragraph.runs) + "\n"

        try:
            # Verificar el tipo de contenido
            has_images = has_image_variables(all_text, context)
            has_conditionals = has_conditional_blocks(all_text)
            has_loops = has_text_level_loops(all_text)
            
            if has_conditionals or has_loops or has_images:
                # Si hay condicionales, bucles o imágenes, renderizar TODO con Jinja2
                # Contenido complejo: render completo (posible pérdida de formatos finos)
                rendered_text = render_text(all_text, context, jinja_env)
                write_text_preserving_formatting(text_frame, rendered_text or "")
                tracer.log_variable(all_text.strip(), (rendered_text or "").strip())
            else:
                # Sólo variables simples: sustituir por run conservando formato
                render_runs_preserving_formatting(text_frame, context, jinja_env)
                tracer.log_variable(all_text.strip(), (text_frame.text or "").strip())

            # Limpiar el text_frame y agregar el texto renderizado
            # while len(text_frame.paragraphs) > 1:
            #     text_frame._element.remove(text_frame._element[-1])

            # paragraph = text_frame.paragraphs[0]
            # while len(paragraph.runs) > 1:
            #     paragraph._element.remove(paragraph.runs[-1]._r)

            # paragraph.runs[0].text = rendered_text

                        # Escritura segura: evita IndexError en runs vacíos

            # try:
            #     text_frame.clear()  # deja un párrafo vacío
            # except Exception as e:
            #     print(f"No se pudo limpiar el text_frame: {e}")
            #     pass
            # text_frame.text = rendered_text or ""

            write_text_preserving_formatting(text_frame, rendered_text or "")
            tracer.log_variable(all_text.strip(), (rendered_text or "").strip())

            #tracer.log_variable(all_text.strip(), rendered_text.strip())

        except Exception as e:
            tracer.log_error(f"Error al renderizar texto '{all_text.strip()}': {e}")