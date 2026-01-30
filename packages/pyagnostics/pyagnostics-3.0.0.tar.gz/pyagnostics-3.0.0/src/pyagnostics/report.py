from collections.abc import Iterable, Iterator, MutableSequence, Sequence
from dataclasses import dataclass, field
from typing import Self

from rich.color import Color
from rich.console import (
    Console,
    ConsoleOptions,
    ConsoleRenderable,
    Group,
    NewLine,
    RenderableType,
    RenderResult,
    RichCast,
    group,
)
from rich.padding import Padding
from rich.segment import Segment
from rich.style import Style
from rich.styled import Styled
from rich.terminal_theme import DIMMED_MONOKAI
from rich.text import Text
from rich.traceback import Stack, Traceback

from pyagnostics.protocols import Diagnostic, SourceMap
from pyagnostics.severity import Severity
from pyagnostics.spans import LabeledSpan, SourceId, SourceSpan


@dataclass
class LabeledSourceBlock:
    source: Text
    title: str | None = None
    start_line: int = 1
    start_char_index: int = 0
    labels: Sequence[LabeledSpan] = field(default_factory=list)

    def __rich_console__(  # noqa: PLR0912, PLR0915
        self: Self, _console: Console, _options: ConsoleOptions
    ) -> RenderResult:
        plain_lines_with_end = self.source.plain.splitlines(keepends=True)
        text_lines = list(self.source.split("\n"))
        if len(text_lines) > len(plain_lines_with_end):
            text_lines = text_lines[: len(plain_lines_with_end)]

        lines_in_src = len(plain_lines_with_end)
        line_number_max_len = len(str(lines_in_src + self.start_line))
        line_numbers_padding = " " * (line_number_max_len + 1)

        if self.title is not None:
            yield Segment(line_numbers_padding)
            yield Segment(f"╭─[{self.title}]\n")
        else:
            yield Segment(line_numbers_padding)
            yield Segment("╭───\n")

        src_line_start_index = self.start_char_index
        available_width = max(1, _options.max_width - (line_number_max_len + 3))

        for i, (line, line_with_end) in enumerate(
            zip(text_lines, plain_lines_with_end)
        ):
            wrapped_lines = line.wrap(
                _console, width=available_width, overflow="fold", no_wrap=False
            )
            wrapped_lines_list: list[Text] = (
                list(wrapped_lines) if wrapped_lines else [Text("")]
            )

            offset = 0
            for j, wrapped_line in enumerate(wrapped_lines_list):
                wrapped_line.end = ""
                wrapped_plain = wrapped_line.plain
                segment_len = len(wrapped_plain)
                segment_start = src_line_start_index + offset
                segment_end = segment_start + segment_len

                labels_in_line = [
                    label
                    for label in self.labels
                    if label.span.start < segment_end and label.span.end > segment_start
                ]
                labels_in_line = sorted(
                    labels_in_line, key=lambda label: label.span.start
                )

                line_number = (
                    f"{str(i + self.start_line).rjust(line_number_max_len)}"
                    if j == 0
                    else " " * line_number_max_len
                )
                yield Segment(line_number, style=Style(dim=True))
                yield Segment(" │ ")
                yield wrapped_line
                yield Segment.line()

                if labels_in_line:
                    for label_row in range(len(labels_in_line) + 1):
                        yield Segment(line_numbers_padding)
                        yield Segment("· ")

                        labels_line_length = 0

                        for k, label in enumerate(
                            labels_in_line[: len(labels_in_line) - label_row + 1]
                        ):
                            label_start = max(label.span.start, segment_start)
                            label_end = min(label.span.end, segment_end)
                            label_len = max(1, label_end - label_start)
                            before_len = (
                                label_start - segment_start - labels_line_length
                            )
                            label_before_middle_len = label_len // 2
                            label_after_middle_len = (
                                label_len - label_before_middle_len - 1
                            )

                            style = Style(
                                color=Color.from_triplet(
                                    DIMMED_MONOKAI.ansi_colors[(k % 7) + 1]
                                )
                            )

                            if label_row == 0:
                                yield Segment(" " * before_len)
                                yield Segment("─" * label_before_middle_len, style)
                                yield Segment("┬", style)
                                yield Segment("─" * label_after_middle_len, style)
                            else:
                                yield Segment(
                                    " " * (before_len + label_before_middle_len)
                                )
                                if k == len(labels_in_line) - label_row:
                                    yield Segment("╰─ ", style)

                                    renderable = label.label
                                    if isinstance(label.label, str):
                                        renderable = Text(label.label, end="")

                                    yield Styled(renderable, style)
                                else:
                                    yield Segment("│", style)
                                    yield Segment(" " * label_after_middle_len)

                            labels_line_length += before_len + label_len

                        yield Segment.line()

                offset += segment_len

            src_line_start_index += len(line_with_end)

        yield Segment(line_numbers_padding)
        yield Segment("╰───\n")


def next_exc(exc: BaseException) -> BaseException | None:
    if exc.__cause__:
        return exc.__cause__
    elif exc.__context__ and not exc.__suppress_context__:
        return exc.__context__
    else:
        return None


def walk_causes_and_stacks(exc: BaseException) -> Iterator[tuple[BaseException, Stack]]:
    cause: BaseException | None = exc
    stacks = Traceback.extract(type(exc), exc, exc.__traceback__).stacks

    while True:
        assert cause is not None
        yield cause, stacks.pop(0)
        cause = next_exc(cause)
        if cause is None:
            break


@dataclass
class CauseList(ConsoleRenderable):
    header: RenderableType | None
    items: Sequence[RenderableType | None]
    style: Style

    def __rich_console__(
        self: Self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        if self.header:
            yield Segment(" × ", style=self.style)  # noqa: RUF001

            lines = console.render_lines(
                self.header,
                new_lines=True,
                options=options.update(
                    max_width=options.max_width - 3,
                    overflow="fold",
                    no_wrap=False,
                ),
            )

            yield from lines[0]
            for i, line in enumerate(lines[1:]):
                if i == len(lines) - 2 and len(self.items) == 0:
                    yield Segment("   ", style=self.style)
                else:
                    yield Segment(" │ ", style=self.style)
                yield from line

        for i, item in enumerate(self.items):
            if item is None:
                yield Segment(" │   ", style=self.style)
                yield NewLine()
                continue

            lines = console.render_lines(
                item,
                options=options.update(
                    max_width=options.max_width - 5,
                    overflow="fold",
                    no_wrap=False,
                ),
            )

            for j, line in enumerate(lines):
                if j == 0:
                    if i < len(self.items) - 1:
                        yield Segment(" ├─▶ ", style=self.style)
                    else:
                        yield Segment(" ╰─▶ ", style=self.style)
                elif i < len(self.items) - 1:
                    yield Segment(" │   ", style=self.style)
                else:
                    yield Segment("     ", style=self.style)
                yield from line
                yield NewLine()


@dataclass
class Report(RichCast):
    diag: Diagnostic
    suppressed_frame_paths: Sequence[str] = field(default_factory=list)

    @group()
    def _render_header(self: Self) -> RenderResult:
        if self.diag.code:
            yield Segment(
                f"{self.diag.severity.title()}: ", style=self.diag.severity.style
            )
            yield Styled(self.diag.code, style=self.diag.severity.style)
            yield NewLine()

    @group()
    def _render_causes(
        self: Self, include_exc_causes: bool = True
    ) -> Iterable[RenderableType]:
        causes: MutableSequence[RenderableType | None] = [*self.diag.context]

        if isinstance(self.diag, BaseException):
            causes_and_stacks: Iterator[tuple[BaseException, Stack]] = (
                walk_causes_and_stacks(self.diag)
            )
            if not include_exc_causes:
                causes_and_stacks = iter([next(causes_and_stacks)])

            first = True
            for exc, stack in causes_and_stacks:
                if first:
                    first = False
                    for frame in stack.frames:
                        if any(
                            frame.filename.startswith(path)
                            for path in self.suppressed_frame_paths
                        ):
                            continue

                        causes.append(
                            f"in File {frame.filename}:{frame.lineno} in {frame.name}"
                        )
                elif isinstance(exc, Diagnostic):
                    cause_report = Report(exc)
                    causes.append(
                        Group(
                            Text.assemble(
                                "Cause" if stack.is_cause else "Context",
                                ": ",
                                style=Severity.ERROR.style,
                                end="",
                            ),
                            Styled(
                                exc.code if exc.code else "unknown",
                                style=exc.severity.style,
                            ),
                            cause_report._render_causes(include_exc_causes=False),
                        )
                    )
                else:
                    nested_causes = []

                    for frame in stack.frames:
                        if any(
                            frame.filename.startswith(path)
                            for path in self.suppressed_frame_paths
                        ):
                            continue

                        nested_causes.append(
                            f"in File {frame.filename}:{frame.lineno} in {frame.name}"
                        )

                    causes.append(
                        Group(
                            Text.assemble(
                                "Cause" if stack.is_cause else "Context",
                                ": ",
                                exc.__class__.__module__,
                                ".",
                                exc.__class__.__name__,
                                style=Severity.ERROR.style,
                            ),
                            CauseList(
                                str(exc),
                                nested_causes,
                                style=self.diag.severity.style,
                            ),
                        )
                    )

        yield CauseList(self.diag.message, causes, style=self.diag.severity.style)

    @group()
    def _render_snippets(self: Self) -> Iterable[RenderableType]:
        if not self.diag.labels or not isinstance(self.diag, SourceMap):
            return
        labels_by_source: dict[SourceId, list[LabeledSpan]] = {}
        for label in self.diag.labels:
            labels_by_source.setdefault(label.source_id, []).append(label)

        for source_id, labels in labels_by_source.items():
            resolved = self.diag.get_source(source_id)
            if resolved is None:
                continue
            source_code, highlighter = resolved

            if not labels:
                continue

            context_spans: list[SourceSpan] = []
            for label in labels:
                span_contents = source_code.read_span(
                    label.span, context_lines_before=2, context_lines_after=2
                )
                context_spans.append(
                    SourceSpan(
                        span_contents.span.start,
                        span_contents.span.end,
                        source_id=span_contents.span.source_id,
                    )
                )

            for merged_span in SourceSpan.union(context_spans):
                span_contents = source_code.read_span(merged_span)
                if highlighter is not None:
                    span_contents = highlighter.highlight(span_contents)
                block_labels = [
                    label
                    for label in labels
                    if label.span.start < merged_span.end
                    and label.span.end > merged_span.start
                ]
                if not block_labels:
                    continue
                yield NewLine()
                yield LabeledSourceBlock(
                    span_contents.text,
                    title=span_contents.name,
                    start_line=span_contents.line,
                    start_char_index=span_contents.span.start,
                    labels=block_labels,
                )

    @group()
    def _render_notes(self: Self) -> Iterable[RenderableType]:
        if self.diag.notes:
            yield NewLine()
            yield from self.diag.notes

    def __rich__(self: Self) -> RenderableType:
        return Padding(
            Group(
                self._render_header(),
                Padding(
                    Group(
                        self._render_causes(),
                        self._render_snippets(),
                        self._render_notes(),
                    ),
                    pad=(0, 1),
                ),
            ),
            pad=(1, 1),
        )
