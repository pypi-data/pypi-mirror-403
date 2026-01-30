"""cyta - cython -a for terminal."""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from Cython.Compiler.Annotate import _parse_code
from rich.console import Console

if TYPE_CHECKING:
    from re import Match

    from rich.text import Text

__version__ = "0.2.3"
__all__ = ["LineInfo", "annotate", "compile_and_parse", "is_pure_c", "main"]

# Display constants
YELLOW_BG = "on rgb(50,45,0)"
LINE_TRUNCATE_FULL = 80
LINE_TRUNCATE_FILTERED = 70
MAX_C_LINES_FULL = 12
MAX_C_LINES_FILTERED = 4
MARKER_OFFSET = 50
MAX_BLOCK_SIZE = 2000
VERBOSE_FULL = 2

# Rich styles for C code (matching Cython's HTML colors)
RICH_STYLES: dict[str, str] = {
    "py_c_api": "red",
    "pyx_c_api": "rgb(255,100,0)",
    "py_macro_api": "rgb(255,112,0)",
    "pyx_macro_api": "rgb(255,112,0)",
}

# Cython score weights
WEIGHT_PY_C_API = 5
WEIGHT_PYX_C_API = 2
WEIGHT_MACRO = 1


@dataclass
class LineInfo:
    """Information about a source line."""

    score: int
    c_code: str


def score_c_code(c_code: str) -> int:
    """Calculate Python interaction score using Cython's formula."""
    calls = {"py_c_api": 0, "pyx_c_api": 0, "py_macro_api": 0, "pyx_macro_api": 0}

    def count(match: Match[str]) -> str:
        group = match.lastgroup
        if group and group in calls:
            calls[group] += 1
        return match.group(0)

    _parse_code(count, c_code)
    return (
        WEIGHT_PY_C_API * calls["py_c_api"]
        + WEIGHT_PYX_C_API * calls["pyx_c_api"]
        + WEIGHT_MACRO * calls["py_macro_api"]
        + WEIGHT_MACRO * calls["pyx_macro_api"]
    )


def colorize_rich(c_code: str) -> Text:
    """Colorize C code for Rich output."""
    from rich.text import Text

    text = Text()
    last = 0

    def collect(match: Match[str]) -> str:
        nonlocal last
        start, end = match.span()
        if start > last:
            text.append(c_code[last:start], style="dim")
        text.append(match.group(0), style=RICH_STYLES.get(match.lastgroup or "", "dim"))
        last = end
        return match.group(0)

    _parse_code(collect, c_code)
    if last < len(c_code):
        text.append(c_code[last:], style="dim")
    return text


def has_python_calls(c_code: str) -> bool:
    """Check if C code contains Python API calls."""
    found = False

    def check(match: Match[str]) -> str:
        nonlocal found
        found = True
        return match.group(0)

    _parse_code(check, c_code)
    return found


def format_c_code(c_block: str, *, full: bool = False) -> list[str]:
    """Format C code block for display."""
    truncate = LINE_TRUNCATE_FULL if full else LINE_TRUNCATE_FILTERED
    max_lines = MAX_C_LINES_FULL if full else MAX_C_LINES_FILTERED

    result: list[str] = []
    for line in c_block.strip().split("\n"):
        s = line.strip()
        if not s or s.startswith(("/*", "*/")):
            continue
        if full:
            result.append(s[: truncate - 3] + "..." if len(s) > truncate else s)
        elif not s.startswith(("/*", "*", "#", "static", "}", "{")) and has_python_calls(s):
            result.append(s[: truncate - 3] + "..." if len(s) > truncate else s)

    seen: set[str] = set()
    unique = [x for x in result if not (x in seen or seen.add(x))]  # type: ignore[func-returns-value]
    return unique[:max_lines]


def parse_c_file(c_path: Path, source_name: str) -> dict[int, LineInfo]:
    """Parse generated C file to extract scores per line."""
    c_content = c_path.read_text()
    pattern = re.compile(r'/\* "' + re.escape(source_name) + r'":(\d+)\s*[\n\r]')
    markers = [(int(m.group(1)), m.end()) for m in pattern.finditer(c_content)]

    info: dict[int, LineInfo] = {}
    for i, (line_num, start) in enumerate(markers):
        if i + 1 < len(markers):
            end = markers[i + 1][1] - MARKER_OFFSET
        else:
            end = min(start + MAX_BLOCK_SIZE, len(c_content))

        block = c_content[start:end]
        cut = block.find("\n  /*")
        if cut > 0:
            block = block[:cut]

        if line_num in info:
            info[line_num].score += score_c_code(block)
            info[line_num].c_code += "\n" + block
        else:
            info[line_num] = LineInfo(score=score_c_code(block), c_code=block)

    return info


def should_highlight(line: str, score: int) -> bool:
    """Check if line should be highlighted."""
    s = line.strip()
    return score > 0 and bool(s) and not s.startswith(("#", "import "))


def compile_and_parse(source_path: Path) -> dict[int, LineInfo] | str:
    """Compile file and parse C output.

    Returns dict mapping line numbers to LineInfo, or error string.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        c_file = Path(tmpdir) / (source_path.stem + ".c")
        result = subprocess.run(
            [sys.executable, "-m", "cython", "-o", str(c_file), str(source_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return f"Cython compilation failed: {result.stderr}"
        return parse_c_file(c_file, source_path.name)


def is_pure_c(source_path: Path) -> bool | str:
    """Check if file compiles to pure C (no Python interaction).

    Returns True if pure C, False if has Python interaction, or error string.
    """
    result = compile_and_parse(source_path)
    if isinstance(result, str):
        return result
    return all(info.score == 0 for info in result.values())


def annotate(source_path: Path, *, verbose: int = 0, raw: bool = False) -> None:
    """Annotate a Cython file with Python interaction highlighting."""
    from rich.syntax import Syntax

    console = Console(no_color=raw, highlight=not raw)
    source_path = source_path.resolve()
    result = compile_and_parse(source_path)

    if isinstance(result, str):
        console.print(f"Error: {result}", style="red")
        return

    lines = source_path.read_text().splitlines()
    w = len(str(len(lines)))

    console.print()
    if raw:
        console.print(source_path.name)
        console.print("* = Python interaction\n")
        syntax = None
    else:
        console.print(f"[bold cyan]{source_path.name}[/bold cyan]")
        console.print("[dim]Yellow = Python interaction[/dim]\n")
        syntax = Syntax("", "python", theme="native", background_color="default")

    for i, line in enumerate(lines, 1):
        info = result.get(i)
        score = info.score if info else 0
        hl = should_highlight(line, score)

        if raw:
            marker = "*" if hl else " "
            console.print(f"{marker} {i:>{w}} | {line}")
        else:
            assert syntax is not None
            code = syntax.highlight(line)
            code.rstrip()
            if hl:
                code.stylize(YELLOW_BG)
            console.print(f" [dim]{i:>{w}}[/dim] | ", end="")
            console.print(code)

        if verbose and hl and info:
            for c in format_c_code(info.c_code, full=(verbose >= VERBOSE_FULL)):
                if raw:
                    console.print(f"  {' ' * w} | > {c}")
                else:
                    console.print(f" {' ' * w} | [dim]>[/dim] ", end="")
                    console.print(colorize_rich(c))

    console.print()


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="cyta",
        description="cython -a for terminal (no HTML/browser needed)",
    )
    parser.add_argument("files", nargs="+", help="Cython files to annotate")
    parser.add_argument("--annotate-fullc", action="store_true", help="Show generated C code")
    parser.add_argument("--raw", action="store_true", help="Plain text (no colors)")

    args = parser.parse_args(argv)
    verbose = VERBOSE_FULL if args.annotate_fullc else 0

    console = Console(stderr=True)
    for f in args.files:
        path = Path(f)
        if not path.exists():
            console.print(f"[red]Error: {path} not found[/red]")
            return 1
        annotate(path, verbose=verbose, raw=args.raw)

    return 0


if __name__ == "__main__":
    sys.exit(main())
