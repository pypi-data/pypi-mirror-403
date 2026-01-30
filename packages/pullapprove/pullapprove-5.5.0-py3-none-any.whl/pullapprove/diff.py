import re
from collections.abc import Generator, Iterator


class DiffFile:
    def __init__(self, *, old_path: str, new_path: str):
        self.old_path = old_path
        self.new_path = new_path

    def __repr__(self) -> str:
        return f"<DiffFile old_path={self.old_path} new_path={self.new_path}>"

    def is_move(self) -> bool:
        return self.old_path != self.new_path


class DiffHunk:
    def __init__(
        self,
        *,
        old_line: int,
        old_length: int | None,
        new_line: int,
        new_length: int | None,
    ):
        self.old_line = old_line
        self.old_length = old_length
        self.new_line = new_line
        self.new_length = new_length


class DiffCode:
    def __init__(
        self,
        *,
        old_line_number: int | None,
        new_line_number: int | None,
        content: str,
        change_type: str,
    ):
        self.old_line_number = old_line_number
        self.new_line_number = new_line_number
        self.content = content
        self.change_type = change_type

    def is_addition(self) -> bool:
        return self.change_type == "+"

    def is_deletion(self) -> bool:
        return self.change_type == "-"

    def is_context(self) -> bool:
        return self.change_type == ""

    @property
    def line_number(self) -> int:
        """For backwards compatibility - returns the appropriate line number."""
        if self.is_deletion():
            return self.old_line_number or 0
        return self.new_line_number or 0

    def __str__(self) -> str:
        return f"{self.line_number}: {self.change_type or ' '}{self.content}"

    def __repr__(self) -> str:
        return f"<DiffCode change_type={self.change_type} old_line={self.old_line_number} new_line={self.new_line_number} content={self.content}>"

    def raw(self) -> str:
        return f"{self.change_type or ' '}{self.content}"


def parse_diff_file_line(line: str) -> DiffFile | None:
    match = re.match(r"^diff --git \w/(.*) \w/(.*)", line)
    if match:
        a_path, b_path = match.groups()
        return DiffFile(
            old_path=a_path.strip(),
            new_path=b_path.strip(),
        )
    return None


def parse_diff_hunk_line(line: str) -> DiffHunk | None:
    match = re.match(r"^@@ -(\d+),?(\d+)? \+(\d+),?(\d+)? @@", line)
    if match:
        old_line, old_length, new_line, new_length = match.groups()
        return DiffHunk(
            old_line=int(old_line),
            old_length=int(old_length) if old_length else None,
            new_line=int(new_line),
            new_length=int(new_length) if new_length else None,
        )
    return None


def iterate_diff_parts(
    diff: Iterator[str] | str,
) -> Generator[DiffFile | DiffCode, None, None]:
    current_file, current_hunk = None, None

    # Keep track of where we are in the hunk as we go
    hunk_minus_line_number, hunk_plus_line_number = 0, 0

    if isinstance(diff, str):
        diff_iterator = diff.splitlines()
    else:
        diff_iterator = diff

    for raw in diff_iterator:
        if new_file := parse_diff_file_line(raw):
            current_file = new_file
            current_hunk = None
            yield new_file  # Yield the new file as we go
        elif current_file:
            if new_hunk := parse_diff_hunk_line(raw):
                current_hunk = new_hunk

                hunk_minus_line_number = current_hunk.old_line
                hunk_plus_line_number = current_hunk.new_line

                # Git may include the first line of context immediately after
                # the second `@@` in the hunk header (e.g. function/context
                # signatures). For example:
                #
                #     @@ -6,7 +6,7 @@ binary, for any purpose, ...
                #
                # In that case the portion after the final `@@` should be
                # treated as an unchanged context line that belongs to the
                # hunk. The existing logic only yields lines that start with
                # a prefix character ("+", "-", or space). To ensure we don't
                # silently drop this first line we detect any trailing text
                # after the hunk header and immediately yield it as a context
                # `DiffCode` line.
                #
                # Find the position of the closing `@@` and capture anything
                # that follows. We purposefully split on the first occurrence
                # of `@@` (after the initial one already matched by the regex)
                # so we don't mis-handle unusual file paths that might contain
                # the same token.
                # If the line contains more than one set of "@@" tokens then
                # any text that appears after the final token represents the
                # first context line of the hunk. Extract that portion and
                # yield it as a normal (unchanged) diff line.
                trailing = ""
                if raw.count("@@") > 1:
                    trailing = raw.split("@@")[-1].lstrip()

                if trailing:
                    yield DiffCode(
                        old_line_number=hunk_minus_line_number,
                        new_line_number=hunk_plus_line_number,
                        content=trailing,
                        change_type="",
                    )

                    # Increment the counters because we just consumed the first
                    # context line for both the old and new versions.
                    hunk_plus_line_number += 1
                    hunk_minus_line_number += 1
            elif current_hunk:
                if raw.startswith("+"):
                    yield DiffCode(
                        old_line_number=None,
                        new_line_number=hunk_plus_line_number,
                        content=raw[1:],
                        change_type="+",
                    )
                    hunk_plus_line_number += 1
                elif raw.startswith("-"):
                    yield DiffCode(
                        old_line_number=hunk_minus_line_number,
                        new_line_number=None,
                        content=raw[1:],
                        change_type="-",
                    )
                    hunk_minus_line_number += 1
                elif raw.startswith(" "):
                    yield DiffCode(
                        old_line_number=hunk_minus_line_number,
                        new_line_number=hunk_plus_line_number,
                        content=raw[1:],
                        change_type="",
                    )
                    hunk_plus_line_number += 1
                    hunk_minus_line_number += 1
                else:
                    continue
            else:
                # Header/meta lines between file and hunk...
                pass
