import dataclasses
from collections.abc import MutableSequence
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Self, cast

from rich.abc import RichRenderable
from rich.console import Group, RenderableType, RichCast

from pyagnostics.protocols import (
    Diagnostic,
    SourceCode,
    SourceCodeHighlighter,
    SourceMap,
)
from pyagnostics.report import Report
from pyagnostics.severity import Severity
from pyagnostics.spans import LabeledSpan, SourceId

_suppressed_frame_paths: MutableSequence[str] = []


def supress_diagnostic_frames(*modules: str | ModuleType) -> None:
    for module in modules:
        match module:
            case str() as module:
                _suppressed_frame_paths.append(module)
            case ModuleType() as module if module.__file__ is not None:
                _suppressed_frame_paths.append(
                    str(Path(module.__file__).parent.resolve())
                )
            case _:
                raise ValueError(f"Unsupported module type: {module}")


@dataclass
class DiagnosticError(RichCast, SourceMap, Exception):
    severity: Severity = Severity.ERROR
    code: RenderableType | None = None
    message: RenderableType | None = None
    labels: list[LabeledSpan] = dataclasses.field(default_factory=list)
    notes: list[RenderableType] = dataclasses.field(default_factory=list)
    context: list[RenderableType] = dataclasses.field(default_factory=list)
    source_map: dict[SourceId, tuple[SourceCode, SourceCodeHighlighter | None]] = (
        dataclasses.field(default_factory=dict)
    )

    def with_context(self: Self, context: RenderableType) -> Self:
        self.context.append(context)
        return self

    def add_source(
        self: Self,
        source_id: SourceId,
        source_code: SourceCode,
        highlighter: SourceCodeHighlighter | None = None,
    ) -> Self:
        if source_id not in self.source_map:
            self.source_map[source_id] = (source_code, highlighter)
        return self

    def get_source(
        self: Self, source_id: SourceId
    ) -> tuple[SourceCode, SourceCodeHighlighter | None] | None:
        return self.source_map.get(source_id)

    def add_note(self: Self, note: str) -> None:
        self.notes.append(note)

    def __rich__(self: Self) -> RenderableType:
        return Report(self, suppressed_frame_paths=_suppressed_frame_paths)


if TYPE_CHECKING:
    _: type[Diagnostic] = DiagnosticError


class DiagnosticErrorGroup(ExceptionGroup[DiagnosticError], SourceMap, RichCast):
    def add_source(
        self: Self,
        source_id: SourceId,
        source_code: SourceCode,
        highlighter: SourceCodeHighlighter | None = None,
    ) -> Self:
        for exception in self.exceptions:
            if isinstance(exception, SourceMap):
                exception.add_source(source_id, source_code, highlighter=highlighter)
        return self

    def get_source(
        self: Self, source_id: SourceId
    ) -> tuple[SourceCode, SourceCodeHighlighter | None] | None:
        for exception in self.exceptions:
            if isinstance(exception, SourceMap):
                resolved = exception.get_source(source_id)
                if resolved is not None:
                    return resolved
        return None

    def __rich__(
        self: Self,
    ) -> RenderableType:
        return Group(
            *[
                cast(RenderableType, exception)
                for exception in self.exceptions
                if isinstance(exception, RichRenderable)
            ]
        )
