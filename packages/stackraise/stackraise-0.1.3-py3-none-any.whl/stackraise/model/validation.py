from typing import NoReturn
from fastapi import HTTPException

def validation_error(msg: str) -> NoReturn:
    """Convención con el frotend para lanzar excepciones de validación desde el backend"""
    raise HTTPException(status_code=400, detail=msg)


