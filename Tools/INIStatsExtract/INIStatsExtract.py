"""
Searches all INI files for fields matching one or more filters and writes every
matching definition, including its parent blocks, to a text file.

Filter syntax: "KEY" or "KEY = VALUE" (case-insensitive, supports * and ? wildcards).
A filter value matches when its words appear as a contiguous run of words in the field value.

Examples:
  python INIStatsExtract.py BuildTime
  python INIStatsExtract.py "Conditions = PLAYER_UPGRADE"
  python INIStatsExtract.py BuildCost BuildTime --all -o costs.txt
"""

import argparse
import fnmatch
import re
from dataclasses import dataclass, field
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_DIR = SCRIPT_DIR.parent.parent
DEFAULT_ROOT = REPO_DIR / "GeneralsZH" / "Data" / "INI"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR / ".Generated"


@dataclass
class Filter:
    text: str
    key: str
    value_words: list[str]

    def matches(self, key: str, value_words: list[str]) -> bool:
        if not fnmatch.fnmatchcase(key.lower(), self.key):
            return False
        count = len(self.value_words)
        if count == 0:
            return True
        for i in range(len(value_words) - count + 1):
            if all(fnmatch.fnmatchcase(value_words[i + k].lower(), self.value_words[k]) for k in range(count)):
                return True
        return False


@dataclass
class Definition:
    path: Path
    lines: list[str]
    start: int
    matched_lines: set[int] = field(default_factory=set)
    matched_filters: set[int] = field(default_factory=set)
    match_count: int = 0


def parse_filter(text: str) -> Filter:
    key, sep, value = text.partition("=")
    key = key.strip()
    if not key:
        raise argparse.ArgumentTypeError(f"Invalid filter: '{text}'")
    return Filter(text.strip(), key.lower(), value.lower().split() if sep else [])


def strip_comment(line: str) -> str:
    for token in (";", "//"):
        pos = line.find(token)
        if pos >= 0:
            line = line[:pos]
    return line.rstrip()


def split_key_value(text: str) -> tuple[str, list[str]]:
    key, sep, value = text.partition("=")
    if sep:
        return key.strip(), value.split()
    words = text.split()
    return words[0], words[1:]


def search_file(path: Path, filters: list[Filter]) -> list[Definition]:
    raw_lines = path.read_text(encoding="latin-1").splitlines()
    lines = [strip_comment(line) for line in raw_lines]
    definitions: list[Definition] = []
    current: Definition | None = None
    stack: list[tuple[int, int]] = []  # (indent, line index)

    for index, line in enumerate(lines):
        text = line.lstrip()
        if not text:
            continue
        indent = len(line) - len(text)
        while stack and stack[-1][0] >= indent:
            stack.pop()
        if text.lower() == "end":
            continue

        if not stack:
            current = Definition(path, lines, index)
            definitions.append(current)

        key, value_words = split_key_value(text)
        hits = {i for i, flt in enumerate(filters) if flt.matches(key, value_words)}
        if hits:
            current.matched_filters |= hits
            current.match_count += 1
            current.matched_lines.add(index)
            current.matched_lines.update(line_index for _, line_index in stack)

        stack.append((indent, index))

    return [d for d in definitions if d.matched_lines]


def default_output_path(filters: list[Filter]) -> Path:
    name = "_".join(re.sub(r"[^A-Za-z0-9]+", "_", f.text).strip("_") for f in filters)
    return DEFAULT_OUTPUT_DIR / f"{name[:150] or 'Result'}.txt"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("filters", nargs="+", type=parse_filter, help='Field filter, e.g. BuildTime or "Conditions = PLAYER_UPGRADE"')
    parser.add_argument("-o", "--output", type=Path, help="Output text file (default: .Generated/<filters>.txt)")
    parser.add_argument("-r", "--root", type=Path, default=DEFAULT_ROOT, help="INI folder to search recursively")
    parser.add_argument("--all", action="store_true", help="Only list definitions that match all filters")
    parser.add_argument("--show-files", action="store_true", help="Write the source file and line above each definition")
    args = parser.parse_args()

    filters: list[Filter] = args.filters
    root: Path = args.root.resolve()
    if not root.is_dir():
        parser.error(f"INI root folder not found: {root}")

    definitions: list[Definition] = []
    for path in sorted(root.rglob("*.ini"), key=lambda p: str(p).lower()):
        definitions.extend(search_file(path, filters))

    if args.all:
        definitions = [d for d in definitions if len(d.matched_filters) == len(filters)]

    definitions.sort(key=lambda d: d.lines[d.start].strip().lower())

    match_count = sum(d.match_count for d in definitions)
    blocks: list[str] = []
    for definition in definitions:
        out = []
        if args.show_files:
            out.append(f"; {definition.path.relative_to(root).as_posix()}:{definition.start + 1}")
        out.extend(definition.lines[i] for i in sorted(definition.matched_lines))
        blocks.append("\n".join(out))

    header = [
        f"; Filters: {' | '.join(f.text for f in filters)}{' (all)' if args.all else ''}",
        f"; Root: {root}",
        f"; Definitions: {len(definitions)}, Matching lines: {match_count}",
    ]

    output: Path = args.output or default_output_path(filters)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(header) + "\n\n" + "\n\n".join(blocks) + "\n", encoding="utf-8")
    print(f"Found {len(definitions)} definitions with {match_count} matching lines")
    print(f"Written to {output}")


if __name__ == "__main__":
    main()
