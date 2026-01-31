from typing import Any, Dict, List, Optional
from jinja2 import Environment, meta, StrictUndefined
import re

def create_jinja_env():
    return Environment(
        undefined=StrictUndefined,
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True
    )

def extract_variables_from_text(text: str, jinja_env: Environment):
    ast = jinja_env.parse(text)
    return meta.find_undeclared_variables(ast)

def extract_slide_loop(text: str) -> Optional[tuple[str, str, str]]:
    #pattern = r"""\{%\s*for\s+(\w+)\s+(of|in)\s+(\w+)\s*%\}"""
    pattern = r"""\{%\s*for\s+(\w+)\s+(of|in)\s+(.+?)\s*%\}"""
    match = re.search(pattern, text)
    if match:
        var, tipo, lista = match.groups()
        return var, lista, tipo
    return None

def extract_image_variables(text: str, context: dict) -> List[str]:
    """
    Extrae variables que son de tipo ImageData del contexto
    """
    
    from .image.model import ImageData

    # Buscar todas las variables en el texto
    pattern = r"""\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)\s*\}\}"""
    variables = re.findall(pattern, text)
    
    # Filtrar solo las que son ImageData
    image_vars = []
    for var in variables:
        # Navegar por variables anidadas (ej: client.logo)
        value = context
        try:
            for part in var.split('.'):
                value = value[part]
            if isinstance(value, ImageData):
                image_vars.append(var)
        except (KeyError, TypeError):
            continue
    
    return image_vars

def has_image_variables(text: str, context: dict) -> bool:
    """
    Verifica si el texto contiene variables de tipo ImageData
    """
    return len(extract_image_variables(text, context)) > 0

def preprocess_text_for_jinja(text: str, context: dict = None) -> str:
    """
    Preprocesa el texto para convertir 'of' a 'in' en bucles de texto
    y remover variables ImageData (se procesan por separado)
    """
    # Convertir {% for var of list %} a {% for var in list %}
    #pattern = r"""(\{%\s*for\s+\w+\s+)of(\s+\w+\s*%\})"""
    pattern = r"""(\{%\s*for\s+\w+\s+)of(\s+.+?\s*%\})"""
    converted_text = re.sub(pattern, r'\1in\2', text)
    
    # Si tenemos contexto, remover variables ImageData
    if context:
        image_vars = extract_image_variables(text, context)
        for var in image_vars:
            # Reemplazar {{imagen_var}} con placeholder vacío
            var_pattern = r"""\{\{\s*""" + re.escape(var) + r"""\s*\}\}"""
            converted_text = re.sub(var_pattern, "", converted_text)
    
    return converted_text

def extract_slide_conditional_block(text: str) -> Optional[Dict[str, Any]]:
    """
    Extrae un bloque condicional completo incluyendo if/elif/else.
    Retorna un diccionario con la estructura del condicional.
    """
    # Patrón para capturar bloques if completos con elif y else opcionales
    pattern = r"""\{%\s*if\s+(.+?)\s*%\}(.*?)(?:\{%\s*elif\s+(.+?)\s*%\}(.*?))*(?:\{%\s*else\s*%\}(.*?))?\{%\s*endif\s*%\}"""
    
    match = re.search(pattern, text, re.DOTALL)
    if match:
        if_condition = match.group(1).strip()
        return {
            'type': 'conditional_block',
            'if_condition': if_condition,
            'has_block_structure': True
        }
    
    # Patrón más simple para detectar si hay una condición en la slide
    simple_pattern = r"""\{%\s*if\s+(.+?)\s*%\}"""
    simple_match = re.search(simple_pattern, text)
    if simple_match:
        condition = simple_match.group(1).strip()
        return {
            'type': 'simple_conditional',
            'condition': condition,
            'has_block_structure': False
        }
    
    return None

def extract_slide_conditional(text: str) -> Optional[str]:
    """
    Extrae la condición de un bloque if en una slide.
    Retorna la condición si encuentra un bloque {% if condition %}
    """
    pattern = r"""\{%\s*if\s+(.+?)\s*%\}"""
    match = re.search(pattern, text)
    if match:
        condition = match.group(1).strip()
        return condition
    return None

def evaluate_condition(condition: str, context: dict, jinja_env: Environment) -> bool:
    """
    Evalúa una condición de Jinja2 contra el contexto dado.
    """
    try:
        # Crear una plantilla simple que evalúe la condición
        template_text = f"{{% if {condition} %}}TRUE{{% else %}}FALSE{{% endif %}}"
        template = jinja_env.from_string(template_text)
        result = template.render(context)
        return result == "TRUE"
    except Exception as e:
        raise ValueError(f"Error evaluando condición '{condition}': {e}")

def evaluate_conditional_block(text: str, context: dict, jinja_env: Environment) -> bool:
    """
    Evalúa un bloque condicional completo con if/elif/else.
    Retorna True si alguna condición se cumple o hay un else.
    """
    try:
        # Preprocesar para convertir 'of' a 'in'
        processed_text = preprocess_text_for_jinja(text)
        # Renderizar el bloque completo y ver si produce contenido
        template = jinja_env.from_string(processed_text)
        result = template.render(context).strip()
        # Si el resultado no está vacío, significa que alguna condición se cumplió
        return bool(result)
    except Exception as e:
        raise ValueError(f"Error evaluando bloque condicional: {e}")

def render_text(text: str, context: dict, jinja_env: Environment) -> str:
    try:
        # Preprocesar para convertir 'of' a 'in' y remover ImageData
        processed_text = preprocess_text_for_jinja(text, context)
        template = jinja_env.from_string(processed_text)
        return template.render(context)
    except Exception as e:
        raise