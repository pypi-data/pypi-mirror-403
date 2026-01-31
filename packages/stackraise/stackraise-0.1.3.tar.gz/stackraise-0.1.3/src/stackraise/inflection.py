from functools import cache

from inflector import English
from slugify import slugify

_english_inflector = English()

@cache
def to_tablename(s: str) -> str:
    return _english_inflector.tableize(s)

@cache
def to_camelcase(s: str) -> str:
    ns = s.rstrip('_')

    camel = _english_inflector.camelize(ns)
    camel = camel[0].lower() + camel[1:]

    return camel + '_' * (len(s) - len(ns))

@cache
def to_slug(s: str) -> str:
    return slugify(s)

@cache
def to_underscore(s: str) -> str:
    return _english_inflector.underscore(s)

