from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "anchor_inject.py"
spec = importlib.util.spec_from_file_location("anchor_inject", SCRIPT)
anchor_inject = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(anchor_inject)


def test_parse_markdown_anchors() -> None:
    markdown = """
<!-- anchor: s001.title -->
Hydronium prefers the air-water interface
<!-- /anchor -->

<!-- anchor: s001.notes.zh -->
这里用中文讲解。
<!-- /anchor -->
"""

    assert anchor_inject.parse_markdown_anchors(markdown) == {
        "s001.title": "Hydronium prefers the air-water interface",
        "s001.notes.zh": "这里用中文讲解。",
    }


def test_injects_markdown_content_into_html_anchor_attributes() -> None:
    markdown = """
<!-- anchor: s001.title -->
Hydronium prefers the air-water interface
<!-- /anchor -->

<!-- anchor: s001.body -->
Interfacial ion distributions challenge the continuum picture.
<!-- /anchor -->
"""
    template = """
<section class="slide">
  <h1 class="slide-title" anchor="s001.title">placeholder</h1>
  <p class="body" anchor="s001.body"></p>
</section>
"""

    rendered = anchor_inject.inject_anchors(markdown, template)

    assert "placeholder" not in rendered
    assert '<h1 class="slide-title" anchor="s001.title">' in rendered
    assert "Hydronium prefers the air-water interface" in rendered
    assert "Interfacial ion distributions challenge the continuum picture." in rendered


def test_escapes_text_content() -> None:
    markdown = """
<!-- anchor: s001.title -->
A < B & C
<!-- /anchor -->
"""
    template = '<h1 anchor="s001.title"></h1>'

    assert anchor_inject.inject_anchors(markdown, template) == (
        '<h1 anchor="s001.title">A &lt; B &amp; C</h1>'
    )


def test_renders_markdown_bullets_into_list_items() -> None:
    markdown = """
<!-- anchor: s001.body -->
- First point
- Second point
<!-- /anchor -->
"""
    template = '<ul anchor="s001.body"></ul>'

    assert anchor_inject.inject_anchors(markdown, template) == (
        '<ul anchor="s001.body"><li>First point</li><li>Second point</li></ul>'
    )


def test_duplicate_markdown_anchor_raises() -> None:
    markdown = """
<!-- anchor: s001.title -->
First
<!-- /anchor -->
<!-- anchor: s001.title -->
Second
<!-- /anchor -->
"""

    with pytest.raises(anchor_inject.AnchorError, match="Duplicate markdown anchor"):
        anchor_inject.parse_markdown_anchors(markdown)


def test_template_missing_markdown_anchor_raises() -> None:
    markdown = """
<!-- anchor: s001.title -->
Title
<!-- /anchor -->
"""
    template = '<h1 anchor="s001.title"></h1><p anchor="s001.body"></p>'

    with pytest.raises(anchor_inject.AnchorError, match="no markdown content"):
        anchor_inject.inject_anchors(markdown, template)


def test_unused_markdown_anchor_raises() -> None:
    markdown = """
<!-- anchor: s001.title -->
Title
<!-- /anchor -->
<!-- anchor: s001.body -->
Body
<!-- /anchor -->
"""
    template = '<h1 anchor="s001.title"></h1>'

    with pytest.raises(anchor_inject.AnchorError, match="not used by template"):
        anchor_inject.inject_anchors(markdown, template)
