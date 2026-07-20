#!/usr/bin/env python3
"""Fill an HTML template from Markdown anchor blocks.

Markdown:
  <!-- anchor: s001.title -->
  Hydronium prefers the air-water interface
  <!-- /anchor -->

HTML:
  <h1 anchor="s001.title"></h1>
"""

from __future__ import annotations

import argparse
import html
import re
from html.parser import HTMLParser
from pathlib import Path

ANCHOR_BLOCK_RE = re.compile(
    r"<!--\s*anchor:\s*(?P<anchor>[A-Za-z0-9_.:-]+)\s*-->\s*"
    r"(?P<body>.*?)"
    r"\s*<!--\s*/anchor\s*-->",
    re.DOTALL,
)


class AnchorError(ValueError):
    """Raised when anchor content or template markup is invalid."""


def parse_markdown_anchors(markdown: str) -> dict[str, str]:
    anchors: dict[str, str] = {}
    for match in ANCHOR_BLOCK_RE.finditer(markdown):
        name = match.group("anchor").strip()
        body = match.group("body").strip()
        if name in anchors:
            raise AnchorError(f"Duplicate markdown anchor: {name}")
        anchors[name] = body
    return anchors


def render_text_for_tag(tag: str, value: str) -> str:
    if tag in {"ul", "ol"}:
        items = [
            line.removeprefix("- ").strip()
            for line in value.splitlines()
            if line.strip()
        ]
        return "".join(f"<li>{html.escape(item)}</li>" for item in items)
    return html.escape(value)


class AnchorTemplateParser(HTMLParser):
    def __init__(self, anchors: dict[str, str]) -> None:
        super().__init__(convert_charrefs=False)
        self.anchors = anchors
        self.parts: list[str] = []
        self.inject_stack: list[tuple[str, str]] = []
        self.used: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        anchor = self._anchor_from_attrs(attrs)
        self.parts.append(self.get_starttag_text() or self._format_starttag(tag, attrs))
        if anchor:
            if anchor not in self.anchors:
                raise AnchorError(f"Template anchor has no markdown content: {anchor}")
            self.inject_stack.append((tag, anchor))
            self.used.add(anchor)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        anchor = self._anchor_from_attrs(attrs)
        if anchor:
            raise AnchorError(f"Self-closing anchored tag cannot receive content: {anchor}")
        self.parts.append(self.get_starttag_text() or self._format_starttag(tag, attrs, True))

    def handle_endtag(self, tag: str) -> None:
        if self.inject_stack and self.inject_stack[-1][0] == tag:
            _, anchor = self.inject_stack.pop()
            self.parts.append(render_text_for_tag(tag, self.anchors[anchor]))
        if not self.inject_stack:
            self.parts.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        if not self.inject_stack:
            self.parts.append(data)

    def handle_entityref(self, name: str) -> None:
        if not self.inject_stack:
            self.parts.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        if not self.inject_stack:
            self.parts.append(f"&#{name};")

    def handle_comment(self, data: str) -> None:
        if not self.inject_stack:
            self.parts.append(f"<!--{data}-->")

    def handle_decl(self, decl: str) -> None:
        self.parts.append(f"<!{decl}>")

    def handle_pi(self, data: str) -> None:
        self.parts.append(f"<?{data}>")

    def result(self) -> str:
        return "".join(self.parts)

    @staticmethod
    def _anchor_from_attrs(attrs: list[tuple[str, str | None]]) -> str | None:
        for key, value in attrs:
            if key == "anchor" and value:
                return value
        return None

    @staticmethod
    def _format_starttag(
        tag: str,
        attrs: list[tuple[str, str | None]],
        self_closing: bool = False,
    ) -> str:
        rendered_attrs = "".join(
            f" {key}" if value is None else f' {key}="{html.escape(value, quote=True)}"'
            for key, value in attrs
        )
        suffix = " /" if self_closing else ""
        return f"<{tag}{rendered_attrs}{suffix}>"


def inject_anchors(markdown: str, template_html: str) -> str:
    anchors = parse_markdown_anchors(markdown)
    parser = AnchorTemplateParser(anchors)
    parser.feed(template_html)
    parser.close()

    missing = sorted(set(anchors) - parser.used)
    if missing:
        raise AnchorError(f"Markdown anchors not used by template: {', '.join(missing)}")

    return parser.result()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("markdown", type=Path, help="Markdown content file")
    parser.add_argument("template", type=Path, help="HTML template file")
    parser.add_argument("-o", "--output", type=Path, help="Filled HTML output path")
    args = parser.parse_args()

    rendered = inject_anchors(
        args.markdown.read_text(encoding="utf-8"),
        args.template.read_text(encoding="utf-8"),
    )
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
