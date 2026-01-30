from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, Self

from rich.text import Text

from pyagnostics.protocols import (
    SourceCode,
    SourceCodeHighlighter,
    SourceMap,
    SourceSpan,
    SpanContents,
)
from pyagnostics.spans import SourceId


@dataclass
class InMemorySpanContents:
    text: Text
    span: SourceSpan
    line: int
    column: int
    line_count: int
    name: str | None


if TYPE_CHECKING:
    _: type[SpanContents] = InMemorySpanContents


@dataclass
class InMemorySource(SourceCode):
    source_code: str
    name: str | None = None

    def read_span(
        self: Self,
        span: SourceSpan,
        context_lines_before: int = 0,
        context_lines_after: int = 0,
    ) -> SpanContents:
        lines = self.source_code.splitlines(keepends=True)

        chars_before = 0

        start_line_idx = None
        for i, line in enumerate(lines):
            if chars_before + len(line) >= span.start:
                start_line_idx = i
                break
            chars_before += len(line)

        if start_line_idx is None:
            raise ValueError("Span start is out of bounds")

        chars_in_lines = 0
        end_line_idx = None
        for i, line in enumerate(lines[start_line_idx:]):
            chars_in_lines += len(line)
            if chars_before + chars_in_lines >= span.end:
                end_line_idx = i + start_line_idx
                break

        if end_line_idx is None:
            raise ValueError("Span end is out of bounds")

        context_start = max(0, start_line_idx - context_lines_before)
        context_end = min(len(lines) - 1, end_line_idx + context_lines_after)

        chars_before_context = sum(len(line) for line in lines[:context_start])
        chars_before_start = sum(len(line) for line in lines[:start_line_idx])
        column = span.start - chars_before_start
        chars_in_lines = sum(
            len(line) for line in lines[context_start : context_end + 1]
        )

        return InMemorySpanContents(
            text=Text("".join(lines[context_start : context_end + 1])),
            span=SourceSpan(
                chars_before_context,
                chars_before_context + chars_in_lines,
                source_id=span.source_id,
            ),
            line=context_start + 1,
            column=column,
            line_count=context_end - context_start,
            name=self.name,
        )


@contextmanager
def attach_diagnostic_source_code(
    source_code: SourceCode,
    highlighter: SourceCodeHighlighter | None = None,
    *,
    source_id: SourceId,
) -> Iterator[SourceId]:
    try:
        yield source_id
    except Exception as e:
        if isinstance(e, SourceMap):
            raise e.add_source(source_id, source_code, highlighter=highlighter)
        raise
