from __future__ import annotations

import re
from datetime import date
from enum import Enum
from functools import cache
from typing import Annotated, Optional, Self, get_args


from fastapi import Query
from pydantic import TypeAdapter, create_model
from pydantic.fields import FieldInfo
from pydantic_core import core_schema

import stackraise.model as model

_QUERY_FILTER_RE = re.compile(r"(?P<op>\w+):(?P<val>.*)")


class QueryFilter[T]:

    class Operator(str, Enum):
        EQ = "eq"
        NE = "neq"
        LT = "lt"
        LTE = "lte"
        GT = "gt"
        GTE = "gte"
        IN = "in"
        LIKE = "like"
        ILIKE = "ilike"

    @classmethod
    def eq(cls, value: T) -> "QueryFilter[T]":
        return cls(cls.Operator.EQ, value)
    
    @classmethod
    def neq(cls, value: T) -> "QueryFilter[T]":
        return cls(cls.Operator.NE, value)
    
    @classmethod
    def lt(cls, value: T) -> "QueryFilter[T]":
        return cls(cls.Operator.LT, value)
    
    @classmethod
    def lte(cls, value: T) -> "QueryFilter[T]":
        return cls(cls.Operator.LTE, value)
    
    @classmethod
    def gt(cls, value: T) -> "QueryFilter[T]":
        return cls(cls.Operator.GT, value)

    @classmethod
    def gte(cls, value: T) -> "QueryFilter[T]":
        return cls(cls.Operator.GTE, value)
    
    @classmethod
    def in_(cls, value: list[T]) -> "QueryFilter[list[T]]":
        return cls(cls.Operator.IN, value)
    
    @classmethod
    def like(cls, value: str) -> "QueryFilter[str]":
        return cls(cls.Operator.LIKE, value)

    operator: Operator
    value: Optional[T | list[T]]

    def __init__(self, operator: Operator, value: T | list[T]):
        self.operator = operator
        self.value = value

    def to_mongo_query_operator(self, annotation: type):
        type_args = get_args(annotation)
        bson = model.TypeAdapter(type_args[0]).dump_python(self.value)
        return _MONGO_QUERY_OPERATOR_MAP[self.operator](bson)

    @classmethod
    def __get_pydantic_core_schema__(cls, filter_alias, handler):
        filter_args = get_args(filter_alias)
        if len(filter_args) != 1:
            raise ValueError(
                f"QueryFilter '{filter_alias}' must have exactly one type argument, got {len(filter_args)}"
            )
        
        inner_type = filter_args[0]


        single_type_adapter = model.TypeAdapter(inner_type)
        list_type_adapter = model.TypeAdapter(list[inner_type])

        def validate(val: str | QueryFilter | None) -> Optional[QueryFilter]:
            if isinstance(val, QueryFilter):
                return val

            # Manejar valores None o vacíos
            if val is None:
                return None
            
            # Convertir a string si no lo es
            if not isinstance(val, str):
                val = str(val)

            val = val.strip()
            
            # Manejar strings vacíos
            if val == "":
                return None

            m = _QUERY_FILTER_RE.match(val)
            if not m:
                raise ValueError(f"Invalid filter string: {val}")

            op = QueryFilter.Operator(m.group("op"))
            val = m.group("val")

            if val == "":
                val = None
            elif op == QueryFilter.Operator.IN:
                val = val.split(",")
                val = list_type_adapter.validate_python(val)  ## Is fine??
            # TODO: like filter restringido a str
            else:
                val = single_type_adapter.validate_strings(val)

            return cls(operator=op, value=val)

        def serialize(filter: QueryFilter) -> str:
            if filter.value is None:
                val = ""
            elif filter.operator == QueryFilter.Operator.IN:
                val = list_type_adapter.serialize(filter.value)
            else:
                val = single_type_adapter.serialize(filter.value)

            return f"{filter.operator.value}:{val}"

        schema = core_schema.json_or_python_schema(
            json_schema=core_schema.no_info_plain_validator_function(validate),
            python_schema=core_schema.no_info_plain_validator_function(validate),
            serialization=core_schema.plain_serializer_function_ser_schema(serialize),
        )

        return schema

    @classmethod
    def __get_pydantic_json_schema__(cls, _, handler):
        return handler(core_schema.str_schema())

    # __pydantic_serializer__ = SchemaSerializer(core_schema.json_schema({"type": "string"}))


_MONGO_QUERY_OPERATOR_MAP = {
    QueryFilter.Operator.EQ: lambda v: {"$eq": v},
    QueryFilter.Operator.NE: lambda v: {"$ne": v},
    QueryFilter.Operator.LT: lambda v: {"$lt": v},
    QueryFilter.Operator.LTE: lambda v: {"$lte": v},
    QueryFilter.Operator.GT: lambda v: {"$gt": v},
    QueryFilter.Operator.GTE: lambda v: {"$gte": v},
    QueryFilter.Operator.IN: lambda v: {"$in": v if isinstance(v, list) else [v]},
    QueryFilter.Operator.LIKE: lambda v: { '$regex': v },
    QueryFilter.Operator.ILIKE: lambda v: { '$regex': v, '$options': 'i' },
}


class QueryFilters(model.Base):

    qs_: Annotated[Optional[str], model.Field(alias='qs')] = None

     
    @classmethod
    @cache
    def for_model(cls, model_class: type[model.Base]) -> type[QueryFilters]:
        # TODO: support for GenericAlias

        def query_filter_of_field(field_info: FieldInfo):

            return Annotated[
                QueryFilter[field_info.annotation],
                Query(
                    None,
                    alias=field_info.alias,
                    description=f"Filter for {field_info.alias} property with {field_info.annotation} type",
                ),
            ]

        fields = {nm: query_filter_of_field(fi) for nm, fi in model_class.model_fields.items()}

        model_class = create_model(
            f"QueryFilters",
            __base__=QueryFilters,
            __module__=model_class.__module__,
            **fields,
        )

        model_class.__qualname__ = f"{model_class.__qualname__}.QueryFilters"

        return model_class


    def to_mongo_query(self, *, prefix: list[str] = []):
        def mk_field_name(field: FieldInfo, field_name):
            return ".".join(prefix + [field.alias or field_name])

        where =  [{
            mk_field_name(field, field_name): query_filter.to_mongo_query_operator(field.annotation)
            for field_name, field in type(self).model_fields.items()
            if (query_filter := getattr(self, field_name, None)) and isinstance(query_filter, QueryFilter)
        }]

        if self.qs_ is not None:
            
            where.append({'$or': [
                { mk_field_name(field, field_name): { '$regex': f'^{self.qs_}', '$options': 'i' }} 
                for field_name, field in type(self).model_fields.items()
                if field.annotation == QueryFilter[str]
            ]})

            # TEXT SEARCH
            # search['$or'].append({ '$text': { '$search': self.qs_,  '$caseSensitive': False, }})

        return {'$and': where}
    

if __name__ == "__main__":
    # from stackraise.persistence.id import Id
    ta = TypeAdapter(QueryFilter[date])
    filter = TypeAdapter(QueryFilter[float]).validate_python("lte:.45")
    print(filter.to_mongo_query)

    class MyModel(model.Base):
        name: Annotated[str, model.Field(alias="n")]
