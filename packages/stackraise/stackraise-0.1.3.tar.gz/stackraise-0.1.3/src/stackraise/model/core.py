from pydantic import BaseModel, ConfigDict, Field
from stackraise import inflection

__all__ = ["Base", 'Field']

class Base(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
        validate_default=True,
        validate_assignment=True,
        serialize_by_alias=True,
        validate_by_alias=True,
        alias_generator=inflection.to_camelcase,
    )

