from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from itertools import count
from threading import Lock
from typing import ClassVar, Self

from rich.console import RenderableType
from rich.style import Style
from rich.text import Span


@dataclass(eq=True, frozen=True, init=False)
class SourceId:
    value: int
    _counter: ClassVar[Iterator[int]] = count(1)
    _lock: ClassVar[Lock] = Lock()

    def __init__(self) -> None:
        with self._lock:
            value = next(self._counter)
        object.__setattr__(self, "value", value)

    # Unsafe constructor for tests. It's the caller's responsibility to avoid `value` collisions.
    @classmethod
    def unsafe_from_value(cls, value: int) -> "SourceId":
        instance = cls.__new__(cls)
        object.__setattr__(instance, "value", value)
        return instance


# Represents a span of codepoints in a source code
@dataclass(eq=True, frozen=True)
class SourceSpan:
    # Starting codepoint index of the span, inclusive
    start: int
    # Ending codepoint index of the span, exclusive
    end: int
    # Source identifier for this span
    source_id: SourceId

    def styled(self: Self, style: Style | str) -> Span:
        return Span(self.start, self.end, style)

    @staticmethod
    def enclose(start: "SourceSpan", end: "SourceSpan") -> "SourceSpan":
        if start.source_id != end.source_id:
            raise ValueError("Cannot enclose spans from different sources")
        return SourceSpan(start.start, end.end, source_id=start.source_id)

    @staticmethod
    def union(spans: "Sequence[SourceSpan]") -> list["SourceSpan"]:
        if not spans:
            return []
        first_source_id = spans[0].source_id
        if any(span.source_id != first_source_id for span in spans):
            raise ValueError("Cannot merge spans from different sources")
        spans = sorted(spans, key=lambda span: span.start)
        merged = [spans[0]]
        for span in spans[1:]:
            last = merged[-1]
            if span.start <= last.end:
                merged[-1] = SourceSpan(
                    last.start, max(last.end, span.end), source_id=first_source_id
                )
            else:
                merged.append(span)
        return merged


@dataclass(eq=True, frozen=True)
class LabeledSpan:
    span: SourceSpan
    label: RenderableType

    @property
    def source_id(self) -> SourceId:
        return self.span.source_id
