#!/usr/bin/env python3
"""Convert a simple Markdown outline into a JSON slide plan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_outline(text: str) -> list[dict[str, object]]:
    slides: list[dict[str, object]] = []
    current: dict[str, object] | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("#"):
            title = line.lstrip("#").strip()
            if title:
                current = {
                    "slide": len(slides) + 1,
                    "title": title,
                    "takeaway": "",
                    "bullets": [],
                    "visual": "",
                    "speaker_intent": "",
                }
                slides.append(current)
            continue

        if current is None:
            current = {
                "slide": len(slides) + 1,
                "title": "Opening",
                "takeaway": "",
                "bullets": [],
                "visual": "",
                "speaker_intent": "",
            }
            slides.append(current)

        if line.startswith(("-", "*")):
            current["bullets"].append(line[1:].strip())  # type: ignore[index, union-attr]
        elif not current["takeaway"]:
            current["takeaway"] = line
        else:
            current["bullets"].append(line)  # type: ignore[index, union-attr]

    return slides


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Markdown outline file")
    parser.add_argument("-o", "--output", type=Path, help="Output JSON path")
    args = parser.parse_args()

    slides = parse_outline(args.input.read_text(encoding="utf-8"))
    payload = {"slides": slides}
    rendered = json.dumps(payload, ensure_ascii=False, indent=2)

    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
