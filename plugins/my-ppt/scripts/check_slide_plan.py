#!/usr/bin/env python3
"""Check a JSON slide plan for common presentation-design issues."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_slides(path: Path) -> list[dict[str, object]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("slides"), list):
        return data["slides"]
    if isinstance(data, list):
        return data
    raise ValueError("Expected a JSON object with a 'slides' list, or a slide list.")


def check_slide(slide: dict[str, object], index: int) -> list[str]:
    title = str(slide.get("title") or "").strip()
    takeaway = str(slide.get("takeaway") or "").strip()
    bullets = slide.get("bullets") or []
    visual = str(slide.get("visual") or "").strip()
    findings: list[str] = []

    label = f"Slide {slide.get('slide') or index + 1}"
    if not title:
        findings.append(f"{label}: missing title.")
    elif len(title) > 90:
        findings.append(f"{label}: title is long; use a shorter action title.")

    if not takeaway:
        findings.append(f"{label}: missing takeaway.")

    if isinstance(bullets, list):
        if len(bullets) > 5:
            findings.append(f"{label}: has {len(bullets)} bullets; split or group content.")
        for bullet in bullets:
            if len(str(bullet)) > 140:
                findings.append(f"{label}: contains an overlong bullet.")

    if not visual:
        findings.append(f"{label}: missing visual recommendation.")

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Slide plan JSON file")
    args = parser.parse_args()

    findings: list[str] = []
    for index, slide in enumerate(load_slides(args.input)):
        findings.extend(check_slide(slide, index))

    if not findings:
        print("No common slide-plan issues found.")
        return 0

    print("\n".join(findings))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
