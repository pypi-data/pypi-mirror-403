from bisect import bisect_left
from decimal import Decimal
from typing import Callable, Generic, Iterator, Mapping, Protocol, Self, TypeVar
from .common import NAN, ONE, ZERO, Decimable, to_decimal


K = TypeVar("K", bound="SupportsLe")


class SupportsLe(Protocol):
    def __le__(self: K, other: K, /) -> bool: ...
    def __lt__(self: K, other: K, /) -> bool: ...


class TimeDict(Generic[K]):
    @classmethod
    def _next_key(cls, key: K) -> K:
        _ = key
        raise NotImplementedError("_next_key must be implemented in subclasses")

    @classmethod
    def _to_string(cls, key: K) -> str:
        return str(key)

    @classmethod
    def _iter_range(cls, start: K, end: K) -> Iterator[K]:
        current = start
        while current <= end:
            yield current
            current = cls._next_key(current)

    @classmethod
    def _inclusive_range(cls, start: K, end: K) -> list[K]:
        return list(cls._iter_range(start, end))

    def _kwargs(self, **kwargs) -> dict:
        return {
            "strict": self._strict,
            "cumulative": self._cumulative,
            **kwargs,
        }

    def __init__(
        self,
        data: Mapping[K, Decimable] | None = None,
        strict: bool = True,
        cumulative: bool = False,
    ) -> None:
        if data is None:
            data = {}
        keys = sorted(data.keys())
        if not keys:
            raise ValueError("Data cannot be empty.")

        if strict:
            expected = keys[0]
            for k in keys:
                if k != expected:
                    raise ValueError(
                        "Data must cover all keys in the contiguous range. "
                        "To disable this check, set strict=False."
                    )
                expected = type(self)._next_key(expected)

        self.start, self.end = keys[0], keys[-1]
        cls = type(self)
        self.data: dict[str, Decimal] = {
            cls._to_string(k): to_decimal(data[k]) for k in keys
        }

        self._cumulative = cumulative
        self._strict = strict
        self._keys_cache: tuple[K, ...] = tuple(keys)

    def _keys(self) -> tuple[K, ...]:
        return self._keys_cache

    @classmethod
    def fill(cls, start: K, end: K, value: Decimable) -> Self:
        v = to_decimal(value)
        data = {k: v for k in cls._iter_range(start, end)}
        obj = cls(data, strict=False, cumulative=False)  # skip re-validation
        obj._strict = True
        return obj

    def get(self, key: K, default: Decimal = NAN) -> Decimal:
        sk = type(self)._to_string(key)
        temp = self.data.get(sk, NAN)
        if temp.is_nan():
            return default
        return temp

    def __getitem__(self, key: K) -> Decimal:
        return self.data[type(self)._to_string(key)]

    def __setitem__(self, key: K, value) -> None:
        cls = type(self)
        sk = cls._to_string(key)
        self.data[sk] = to_decimal(value)

        # maintain sorted logical key cache (K) while storing string keys in dict
        keys = list(self._keys_cache)
        i = bisect_left(keys, key)
        if i == len(keys) or keys[i] != key:
            keys.insert(i, key)
            self._keys_cache = tuple(keys)
            self.start, self.end = keys[0], keys[-1]

    def crop(
        self,
        start: K | None = None,
        end: K | None = None,
        initial_value: Decimable = NAN,
    ) -> Self:
        if start is None and end is None:
            return self

        s = start if start is not None else self.start
        e = end if end is not None else self.end
        cls = type(self)

        if self._strict and s >= self.start and e <= self.end:
            return cls(
                {k: self.data[cls._to_string(k)] for k in self._keys() if s <= k <= e},
                **self._kwargs(strict=True),
            )

        init = to_decimal(initial_value)
        return cls(
            {k: self.get(k, init) for k in cls._iter_range(s, e)},
            **self._kwargs(strict=True),
        )

    def non_negative(self) -> Self:
        cls = type(self)
        out: dict[K, Decimal] = {}
        for k in self._keys():
            v = self.data[cls._to_string(k)]
            out[k] = v if (not v.is_nan() and v >= ZERO) else ZERO
        return cls(out, **self._kwargs())

    def sum(self, start: K | None = None, end: K | None = None) -> Decimal:
        s = start if start is not None else self.start
        e = end if end is not None else self.end
        total = ZERO
        cls = type(self)
        for k in self._keys():
            if k < s:
                continue
            if k > e:
                break
            v = self.data[cls._to_string(k)]
            if not v.is_nan():
                total += v
        return total

    def _binary_op(
        self,
        other: Decimable | Self,
        op: Callable[[Decimal, Decimal], Decimal],
        neutral: Decimal,
    ) -> Self:
        cls = type(self)

        if isinstance(other, cls):
            other_get = other.data.get
            out: dict[K, Decimal] = {}
            for k in self._keys():
                sk = cls._to_string(k)
                ov = other_get(sk, NAN)
                out[k] = op(self.data[sk], ov if not ov.is_nan() else neutral)
            return cls(out, **self._kwargs())

        if isinstance(other, Decimable):
            other_value = to_decimal(other)
            out = {
                k: op(self.data[cls._to_string(k)], other_value) for k in self._keys()
            }
            return cls(out, **self._kwargs())

        raise TypeError(
            "Unsupported operand type(s) for operation: "
            f"'{type(self)}' and '{type(other)}'"
        )

    def __mul__(self, other: Decimable | Self) -> Self:
        return self._binary_op(other, lambda x, y: x * y, ONE)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __neg__(self) -> Self:
        return self * Decimal("-1")

    def __add__(self, other: Decimable | Self) -> Self:
        return self._binary_op(other, lambda x, y: x + y, ZERO)

    def __radd__(self, other: Decimable | Self) -> Self:
        return self.__add__(other)

    def __sub__(self, other: Decimable | Self) -> Self:
        return self._binary_op(other, lambda x, y: x - y, ZERO)

    def __rsub__(self, other: Decimable | Self) -> Self:
        return (-self).__add__(other)

    def __truediv__(self, other: Decimable | Self) -> Self:
        return self._binary_op(other, lambda x, y: x / y, ONE)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return False
        for sk in set(self.data.keys()).union(other.data.keys()):
            s = self.data.get(sk, NAN)
            o = other.data.get(sk, NAN)
            if s.is_nan() and o.is_nan():
                continue
            if s != o:
                return False
        return True

    def __or__(self, other: Self) -> Self:
        if not isinstance(other, type(self)):
            raise TypeError(
                "Unsupported operand type(s) for |: " f"'TimeDict' and '{type(other)}'"
            )

        strict = (
            self._strict
            and other._strict
            and (
                self._next_key(self.end) == other.start
                or self._next_key(other.end) == self.start
            )
        )
        if self._cumulative != other._cumulative:
            raise ValueError("Cannot merge TimeDicts with different cumulative states.")
        cumulative = self._cumulative

        cls = type(self)
        merged_keys = sorted(set(self._keys()).union(other._keys()))
        merged_data: dict[K, Decimal] = {}
        for k in merged_keys:
            sk = cls._to_string(k)
            if sk in other.data:
                merged_data[k] = other.data[sk]
            else:
                merged_data[k] = self.data[sk]

        return cls(merged_data, **self._kwargs(strict=strict, cumulative=cumulative))

    def __str__(self) -> str:
        cls = type(self)
        return "\n".join(f"{k}: {self.data[cls._to_string(k)]}" for k in self._keys())

    def __repr__(self) -> str:
        return f"{self.data!r}"

    def to_array(self) -> list[Decimal]:
        cls = type(self)
        return [self.data[cls._to_string(k)] for k in self._keys()]

    def to_dict(self) -> dict[str, Decimal]:
        return self.data.copy()

    def average(self) -> Decimal:
        total = ZERO
        n = 0
        for v in self.data.values():
            if not v.is_nan():
                total += v
                n += 1
        return total / Decimal(n) if n else ZERO

    def to_cumulative(self, holes_on_none=True) -> Self:
        if self._cumulative:
            raise ValueError("TimeDict is already cumulative.")
        running_total = ZERO
        cumulative_data: dict[K, Decimal] = {}
        cls = type(self)
        for k in self._keys():
            v = self.data[cls._to_string(k)]
            if v.is_nan():
                cumulative_data[k] = NAN if holes_on_none else running_total
            else:
                running_total += v
                cumulative_data[k] = running_total
        return cls(cumulative_data, **self._kwargs(cumulative=True))

    def to_incremental(self, holes_on_none=True) -> Self:
        if not self._cumulative:
            raise ValueError("TimeDict is not cumulative.")
        prev = ZERO
        incremental_data: dict[K, Decimal] = {}
        cls = type(self)
        for k in self._keys():
            v = self.data[cls._to_string(k)]
            if v.is_nan():
                incremental_data[k] = NAN if holes_on_none else ZERO
            else:
                incremental_data[k] = v - prev
                prev = v
        return cls(incremental_data, **self._kwargs(cumulative=False))
