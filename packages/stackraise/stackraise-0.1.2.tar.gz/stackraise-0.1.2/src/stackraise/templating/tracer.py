import logging
from time import perf_counter

logger = logging.getLogger("pptx_template_engine")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter("[PPTX-TEMPLATE] %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


class Tracer:
    """Tracer genérico para motores de plantillas"""
    
    def __init__(self, logger_name: str = "template_engine"):
        self.start_time = None
        self.logger = logging.getLogger(logger_name)
        if not self.logger.handlers:
            self._setup_logger()
    
    def _setup_logger(self):
        """Configura el logger si no está configurado"""
        self.logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(f"[{self.logger.name.upper()}] %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def start(self, engine_type: str = "plantilla"):
        """Inicia el trazado"""
        self.start_time = perf_counter()
        self.logger.info(f"Inicio del render de {engine_type}")

    def end(self):
        """Finaliza el trazado"""
        duration = perf_counter() - self.start_time
        self.logger.info(f"Render finalizado en {duration:.2f} segundos")

    def log_variable(self, var: str, value: any):
        """Registra el renderizado de una variable"""
        self.logger.debug(f"Variable '{{ {var} }}' → {value}")

    def log_duplication(self, item_idx: int, count: int, item_type: str = "elemento"):
        """Registra la duplicación de elementos"""
        self.logger.info(f"{item_type.capitalize()} {item_idx} duplicado {count} veces por bucle")

    def log_conditional(self, item_idx: int, condition: str, result: bool, item_type: str = "elemento"):
        """Registra la evaluación de condicionales"""
        self.logger.info(f"Condicional '{condition}' evaluada como {result} en {item_type} {item_idx}")

    def log_error(self, message: str):
        """Registra un error"""
        self.logger.error(message)

    def log_info(self, message: str):
        """Registra información general"""
        self.logger.info(message)