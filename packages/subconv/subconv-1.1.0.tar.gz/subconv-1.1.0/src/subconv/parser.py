import re
from pathlib import Path

from .core.models import SubtitleBlock

TIMESTAMP_PATTERN = re.compile(r"\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}")


def parse_srt(content: str) -> list[SubtitleBlock]:
    blocks: list[SubtitleBlock] = []
    lines = content.strip().split("\n")
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if not line.isdigit():
            i += 1
            continue

        number = int(line)
        timestamp = lines[i + 1].strip() if i + 1 < len(lines) else ""

        text_lines: list[str] = []
        j = i + 2

        while j < len(lines) and lines[j].strip() and not lines[j].strip().isdigit():
            next_line = lines[j].strip()
            if TIMESTAMP_PATTERN.match(next_line):
                break
            text_lines.append(next_line)
            j += 1

        blocks.append(
            SubtitleBlock(
                number=number,
                timestamp=timestamp,
                text=" ".join(text_lines),
            )
        )
        i = j

    return blocks


def format_srt(blocks: list[SubtitleBlock]) -> str:
    return "\n\n".join(block.to_srt_format() for block in blocks)


def read_srt(path: Path | str) -> list[SubtitleBlock]:
    return parse_srt(Path(path).read_text(encoding="utf-8"))


def write_srt(path: Path | str, blocks: list[SubtitleBlock]) -> None:
    Path(path).write_text(format_srt(blocks), encoding="utf-8")
