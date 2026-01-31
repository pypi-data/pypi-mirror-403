from __future__ import annotations
from typing_extensions import deprecated

from bson import ObjectId
from bson.errors import InvalidId
from pydantic_core import core_schema, SchemaSerializer
from stackraise.model.validation import validation_error

__all__ = ["Id"]

class Id(ObjectId):
    _GENERATE_NEW = object()  # Sentinel para generar nuevo ID
    
    def __init__(self, value=None):
        # Permitir generación explícita de nuevo ID con sentinel
        if value is Id._GENERATE_NEW:
            super().__init__()
            return
        # Evitar que None o vacío generen un ObjectId aleatorio accidentalmente
        if value is None:
            raise ValueError("Valor no seleccionado")
        try:
            super().__init__(value)
        except InvalidId as e:
            raise ValueError(*e.args) from InvalidId

    @classmethod
    def new(cls):
        """Genera un nuevo ObjectId único."""
        return cls(cls._GENERATE_NEW)

    @classmethod
    @deprecated("you must not use this method")
    def from_str(cls, val: str):
        assert isinstance(val, str), f"from_str receive {val}"
        return cls(val)

    @classmethod
    @deprecated("you must not use this method")
    def from_oid(cls, val: Id | ObjectId | str):
        # assert isinstance(val, ObjectId), f"Id from python is {val}"
        return val if isinstance(val, cls) else cls(val)

    @property
    def created_at(self):
        return self.generation_time

    def to_mongo_query(self): # query protocol
        return {"_id": self}
    
    @property
    def value(self) -> str:
        """Return the string representation of the Id"""
        return str(self)

    SCHEMA = core_schema.json_or_python_schema(
        # JSON
        json_schema=core_schema.no_info_plain_validator_function(
            lambda s: Id.from_str(s),
        ),
        # PYTHON
        python_schema=core_schema.no_info_plain_validator_function(
            lambda v: Id.from_oid(v),
        ),
        serialization=core_schema.plain_serializer_function_ser_schema(
            str, when_used="json"  # as str
        ),
    )

    __pydantic_serializer__ = SchemaSerializer(SCHEMA)

    @classmethod
    def __get_pydantic_core_schema__(cls, *_):
        return cls.SCHEMA

    @classmethod
    def __get_pydantic_json_schema__(cls, _, handler):
        # return {"type": "string"}
        return handler(core_schema.str_schema())
