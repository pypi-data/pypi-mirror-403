# %%
from __future__ import annotations

import re
from dataclasses import replace
from datetime import UTC
from datetime import date as Date
from datetime import datetime as DateTime
from datetime import time as Time
from datetime import timedelta as TimeDelta
from datetime import timezone as TimeZone
from typing import Optional, TypeAlias

from pydantic.dataclasses import dataclass

TimeDeltaParseable: TypeAlias = int | str | TimeDelta


DateTimeParseable: TypeAlias = int | str | Date | DateTime


@dataclass(frozen=True, slots=True)
class TimeRange:
    start: DateTime
    stop: DateTime

    @property
    def is_for_an_exact_day(self) -> Optional[Date]:
        if _datetime_is_day_exact(self.start) and self.stop == _datetime_next_day(
            self.start
        ):
            return self.start.date()

    @property
    def is_for_exact_days(self) -> bool:
        return _datetime_is_day_exact(self.start) and _datetime_is_day_exact(self.stop)

    @property
    def is_for_an_exact_month(self) -> bool:
        return _datetime_is_month_exact(self.start) and self.stop == _datetime_next_month(
            self.start
        )

    @property
    def is_for_exact_months(self) -> bool:
        return _datetime_is_month_exact(self.start) and _datetime_is_month_exact(
            self.stop
        )

    @property
    def is_for_an_exact_year(self) -> bool:
        return _datetime_is_year_exact(self.start) and self.stop == _datetime_next_year(
            self.start
        )

    @property
    def is_for_exact_years(self) -> bool:
        return _datetime_is_year_exact(self.start) and _datetime_is_year_exact(self.stop)

    @property
    def extent(self) -> TimeDelta:
        return self.stop - self.start

    @classmethod
    def of(cls, s: TimeRangeParseable):
        if isinstance(s, TimeRange):
            return s
        if isinstance(s, str):
            return _parse_timerange(s)

        raise ValueError(f"Invalid TimeRange string: {s}")

    def __str__(self):
        if self.is_for_an_exact_year:
            fmt = f"{self.start.year}"
        elif self.is_for_an_exact_month:
            fmt = f"{self.start.year}-{self.start.month:02}"
        elif self.is_for_an_exact_day:
            fmt = f"{self.start.date()}"
        else:
            fmt = f"{_repr_datetime(self.start)}..{_repr_datetime(self.stop)}"

        return fmt

    @property
    def duration(self) -> TimeDelta:
        return self.stop - self.start

    def __contains__(self, dt: DateTime):
        return self.start <= dt < self.stop

    def replace(self, **kwargs):
        return replace(self, **kwargs)

    @classmethod
    def overlap(cls, a: TimeRange, b: TimeRange) -> Optional[TimeRange]:
        start = max(a.start, b.start)
        stop = min(a.stop, b.stop)
        if start < stop:
            return cls(start=start, stop=stop)


TimeRangeParseable: TypeAlias = str | TimeRange

# Expresiones regulares
DELTA_REGEX = re.compile(
    r"^(?:(?P<days>\d+)d)?\s?"  # Días opcionales
    r"(?:(?P<hours>\d+)h)?\s?"  # Horas opcionales
    r"(?:(?P<minutes>\d+)m)?\s?"  # Minutos opcionales
    r"(?:(?P<seconds>\d+)s)?$\s?"  # Segundos opcionales
)


def _parse_timedelta(s: TimeDeltaParseable) -> TimeDelta:
    if isinstance(s, TimeDelta):
        return s
    if isinstance(s, int):
        return TimeDelta(milliseconds=s)

    match = DELTA_REGEX.match(s)
    if not match:
        raise ValueError(f"Invalid timedelta string: {s}")

    return TimeDelta(
        **{key: int(value) for key, value in match.groupdict(default="0").items()}
    )


DATE_REGEXES = [
    re.compile(r"^(?P<year>\d{4})$"),  # Solo año
    re.compile(r"^(?P<year>\d{4})-(?P<month>\d{2})$"),  # Año y mes
    re.compile(r"^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})$"),  # Año, mes y día
    re.compile(
        r"^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})T(?P<hour>\d{2}):(?P<minute>\d{2})(?::(?P<second>\d{2}))?$"
    ),  # Fecha y hora
]


def _parse_datetime(dt: DateTimeParseable) -> DateTime:
    if isinstance(dt, int):
        return DateTime.fromtimestamp(dt).replace(tzinfo=TimeZone.utc)
    elif isinstance(dt, str):
        try:
            for regex in DATE_REGEXES:
                if match := regex.match(dt):
                    components = match.groupdict()
                    return DateTime(
                        year=int(components["year"]),
                        month=int(components.get("month", 1)),
                        day=int(components.get("day", 1)),
                        hour=int(components.get("hour", 0)),
                        minute=int(components.get("minute", 0)),
                        second=int(components.get("second", 0)),
                        tzinfo=UTC,
                    )
            raise ValueError(f"Invalid date time string: {dt}")

        except:
            dt = Date.fromisoformat(dt)

    if isinstance(dt, Date):
        return DateTime.combine(dt, Time.min).replace(tzinfo=UTC)
    elif isinstance(dt, DateTime):
        return DateTime.fromtimestamp(dt.timestamp()).replace(tzinfo=UTC)
    else:
        raise ValueError(f"Invalid type {type(dt)}")


RANGE_REGEX = re.compile(
    r"^"
    # Rango explícito "start .. stop"
    r"((?P<start>.+?)\s*\.\.\s*(?P<stop>.+?)(\s)?)"
    r"$"
)

RANGE_SEP = re.compile(r"[\s_]+")


def _parse_timerange(input_str: str) -> TimeRange:
    """
    Parsea una cadena de entrada para determinar el rango de tiempo y el delta.
    """
    # Detectar rango explícito
    range_match = RANGE_REGEX.match(input_str)
    if range_match:
        start = _parse_datetime(range_match.group("start"))
        stop = _parse_datetime(range_match.group("stop"))
        return TimeRange(start=start, stop=stop)

    # Detectar rango implícito (un solo valor)
    start = _parse_datetime(input_str)
    if len(input_str) == 4:  # Año
        stop = _datetime_next_year(start)
    elif len(input_str) == 7:  # Año y mes
        stop = _datetime_next_month(start)
    elif len(input_str) == 10:  # Año, mes y día
        stop = _datetime_next_day(start)
    else:
        raise ValueError(f"Invalid TimeRange string: {input_str}")

    return TimeRange(start=start, stop=stop)


def _repr_timedelta(time_delta: TimeDelta):
    parts = []
    if time_delta < TimeDelta():
        time_delta = -time_delta
        parts.append("-")

    weeks, days = divmod(time_delta.days, 7)
    hours, seconds = divmod(time_delta.seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    if weeks:
        parts.append(f"{weeks}w")
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds:
        parts.append(f"{seconds}s")

    return "".join(parts)


def _repr_datetime(dt: DateTime) -> str:
    if _datetime_is_year_exact(dt):
        return str(dt.year)
    if _datetime_is_month_exact(dt):
        return f"{dt.year}-{dt.month:02}"
    if _datetime_is_day_exact(dt):
        return str(dt.date())
    return dt.isoformat()


def _datetime_is_day_exact(dt: DateTime) -> bool:
    return dt.time() == Time.min

def _datetime_is_month_exact(dt: DateTime) -> bool:
    return dt.day == 1 and _datetime_is_day_exact(dt)

def _datetime_is_year_exact(dt: DateTime) -> bool:
    return dt.month == 1 and _datetime_is_month_exact(dt)

def _datetime_next_day(dt: DateTime) -> DateTime:
    return dt + TimeDelta(days=1)

def _datetime_next_month(dt: DateTime) -> DateTime:
    if dt.month == 12:
        return dt.replace(year=dt.year + 1, month=1)
    return dt.replace(month=dt.month + 1)

def _datetime_next_year(dt: DateTime) -> DateTime:
    return dt.replace(year=dt.year + 1)


# Test cases
if __name__ == "__main__":
    # assert _parse_timedelta("1d") == TimeDelta(days=1)
    # assert _parse_timedelta("1d 2h 3m 4s") == TimeDelta(
    #     days=1, hours=2, minutes=3, seconds=4
    # )
    # assert _parse_timedelta("1d 2h 3m") == TimeDelta(days=1, hours=2, minutes=3)

    assert TimeRange.of("2024").is_for_an_exact_year

    examples = [
        "2024",  # Año completo, paso predeterminado (1 día)
        "2024-01",  # Mes completo, paso predeterminado (1 día)
        "2024-01-01",  # Día completo, paso predeterminado (1 día)
        "2024-01-01T12:00:00",  # Fecha y hora exacta
        "2024-01 .. 2024-07",  # Rango de un año, paso de 1 hora
        "2024-01-01 .. 2024-07-01",  # Rango explícito con delta
    ]

    for example in examples:
        try:
            result = TimeRange.of(example)
            print(f"Input: {example}\nParsed: {result}\n")
        except ValueError as e:
            print(f"Input: {example}\nError: {e}\n")

# %%
