from datetime import date, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Iterator

from .timedict import TimeDict

from .common import ZERO

if TYPE_CHECKING:
    from .yeardict import YearDict

DateKey = str | date


class DateDict(TimeDict[DateKey]):
    @classmethod
    def _next_key(cls, key: DateKey) -> DateKey:
        if isinstance(key, str):
            key_date = date.fromisoformat(key)
        else:
            key_date = key
        next_date = key_date + timedelta(days=1)
        return next_date.strftime("%Y-%m-%d")

    @classmethod
    def _to_string(cls, key: DateKey) -> str:
        return str(key) if isinstance(key, str) else key.strftime("%Y-%m-%d")

    @classmethod
    def _iter_range(cls, start: DateKey, end: DateKey) -> Iterator[DateKey]:
        if isinstance(start, str):
            start_date = date.fromisoformat(start)
        else:
            start_date = start
        if isinstance(end, str):
            end_date = date.fromisoformat(end)
        else:
            end_date = end

        current = start_date
        while current <= end_date:
            yield current.strftime("%Y-%m-%d")
            current += timedelta(days=1)

    def to_yeardict(self) -> "YearDict":
        """
        Convert the DateDict to a YearDict by summing values for each year.
        """
        from .yeardict import YearDict

        year_data: dict[int, Decimal] = {}
        for k, v in self.data.items():
            year = int(k[:4]) if isinstance(k, str) else k.year
            year_data[year] = year_data.get(year, ZERO) + v
        return YearDict(year_data)

    def to_dict(self) -> dict[str, Decimal]:
        return {str(k): v for k, v in self.data.items()}
