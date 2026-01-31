from readline import insert_text
from typing import Optional, Self
from pydantic import validate_email, EmailStr
from pydantic_core import core_schema
from dataclasses import dataclass

@dataclass
class NameEmail:
    email: EmailStr
    name: Optional[str] = None

    @classmethod
    def from_str(cls, value: str) -> Self:
        name, email = validate_email(value)
        return cls(name=name, email=email)

    def __str__(self):
        if not self.name:
            return self.email
        return f"{self.name} <{self.email}>"


    # @classmethod
    # def __get_pydantic_core_schema__(cls, filter_alias, handler):

    #     def validate(val: str | dict | NameEmail) -> NameEmail:
            
    #         if isinstance(val, str):
    #             return NameEmail.from_string(val)
            
    #         if isinstance(val, dict):
    #             return cls(name=val.get("name", None), email=EmailStr(val.get("email")))

    #         return val

    #     def serialize(name_email: NameEmail) -> str:
    #         return str(name_email)

    #     schema = core_schema.json_or_python_schema(
    #         json_schema=core_schema.no_info_plain_validator_function(validate),
    #         python_schema=core_schema.no_info_plain_validator_function(validate),
    #         serialization=core_schema.plain_serializer_function_ser_schema(serialize),
    #     )

    #     return schema
