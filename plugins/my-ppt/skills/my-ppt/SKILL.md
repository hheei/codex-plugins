---
name: my-ppt
description: Design, rewrite, review, and production-plan PowerPoint or slide decks. Use when the user asks for PPT, slides, presentation structure, deck design, speaker flow, visual direction, slide review, or turning notes into a deck.
---

# My PPT

Use this skill for presentation work where the output should become a clear, visually disciplined slide deck.

## Default Behavior

- Answer in the user's language.
- For group-meeting decks, use Simplified Chinese for workflow discussion, English for PPT-facing materials, and Chinese for speaker notes or oral delivery guidance.
- Start from the audience, decision, message, and presentation setting.
- Prefer one clear idea per slide.
- Make the first useful artifact quickly: brief, outline, slide plan, critique, or production checklist.
- Keep the deck practical to build in PowerPoint, Keynote, Google Slides, or Python-generated PPTX.
- When files are involved, inspect the latest file before proposing edits.
- For existing group-meeting HTML/PPTX production, also read `references/ppt-maker-reviewer-lessons.md`.

## Existing Deck Safety

- Before editing an existing deck, HTML slide, Markdown source, preview image, PPTX, or PDF, create a recoverable backup and report its path.
- Work one slide at a time: read the latest slide file, back it up, edit it, render/check only that slide, then stop for review.
- Do not bulk-regenerate all HTML, overwrite all previews, or replace handcrafted per-slide design with a uniform template unless the user explicitly requests a full-deck operation.
- Do not use a content Markdown file such as `slide-content.md` or `content-review.md` to backfill every HTML slide in one pass.
- If the user explicitly requests a full-deck export or rebuild, first make a full backup, test on one slide, then proceed in small batches with a change list.

## Deck Quality Bar

- Story: the audience can repeat the core message after one pass.
- Flow: every slide earns its place and advances the decision.
- Visual hierarchy: title, evidence, and takeaway are immediately distinguishable.
- Density: avoid paragraphs; use grouped labels, charts, diagrams, and short evidence blocks.
- Consistency: typography, color, spacing, captions, and chart treatments are deliberate.
- Delivery: speaker notes and transitions support the presenter instead of duplicating the slide.

## Workflow Routing

- Group meeting PPT from scratch: read `workflows/group-meeting-deck.md`.
- Existing group-meeting HTML/PPTX production: read `references/ppt-maker-reviewer-lessons.md`.
- New deck from rough notes: read `workflows/new-deck.md`.
- Redesign or polish an existing deck: read `workflows/redesign-deck.md`.
- Review a deck or outline: read `workflows/review-deck.md`.
- Storyline prompt: use `prompts/storyline.md`.
- Visual direction prompt: use `prompts/visual-direction.md`.
- Critique prompt: use `prompts/deck-critique.md`.

## Script Helpers

Use plugin scripts when they help:

```bash
python3 scripts/outline_to_slide_plan.py input.md
python3 scripts/check_slide_plan.py slide-plan.json
```

`outline_to_slide_plan.py` turns a Markdown outline into a JSON slide plan. `check_slide_plan.py` flags common slide-planning issues such as long titles, missing takeaways, and overcrowded bullets.

## Output Shape

For most deck-planning tasks, return:

1. Core message
2. Audience and decision
3. Slide-by-slide plan
4. Visual system
5. Open questions or production next steps

For review tasks, return findings first, ordered by severity, with slide references when available.
