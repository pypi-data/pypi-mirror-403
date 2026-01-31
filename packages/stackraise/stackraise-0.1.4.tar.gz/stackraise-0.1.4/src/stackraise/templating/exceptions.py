class PptxTemplateEngineError(Exception):
    """Base para errores del motor de plantillas PPTX"""
    pass


class TemplateSyntaxError(PptxTemplateEngineError):
    pass


class UndefinedVariableError(PptxTemplateEngineError):
    pass


class ContextError(PptxTemplateEngineError):
    pass


class TemplateNotFoundError(PptxTemplateEngineError):
    pass


class RenderError(PptxTemplateEngineError):
    pass