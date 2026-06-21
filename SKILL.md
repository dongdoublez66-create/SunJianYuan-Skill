---
name: sun-jianyuan-style
description: Draft, revise, diagnose, or transform neuroscience and biomedical research writing into a Sun Jianyuan aligned academic style. Use when the user asks to write or polish papers, abstracts, introductions, results, discussions, cover letters, reviewer responses, grant-style summaries, oral presentation scripts, slide narration, or Chinese-to-English academic prose in a style consistent with Sun Jianyuan's published scientific writing and inferred academic speaking voice.
---

# Sun Jianyuan Style

## Purpose

Use this skill to help the user write or revise scientific text with the high-level rhetorical habits observed in Sun Jianyuan's published papers: mechanism-first framing, precise synaptic/neural terminology, restrained significance claims, evidence-led paragraphing, and calibrated uncertainty.

Do not impersonate Sun Jianyuan, claim that he wrote the text, or copy distinctive source sentences. Align with the style profile while preserving the user's actual science, data, and authorship.

## Evidence Boundary

This skill cannot fully reproduce Sun Jianyuan's real spoken manner unless the user provides actual speech evidence such as talk recordings, transcripts, interviews, course audio, lab-meeting notes, or Q&A records. Without those materials, generate an inferred academic presentation voice derived from published writing: mechanism-first, data-bound, concise, and cautious.

When the user asks for "speaking style", explicitly treat it as "paper-style scientific logic converted into oral reporting style" unless speech samples are provided. If the user provides speech samples, first extract recurring discourse markers, pacing, self-corrections, audience-facing explanations, and Q&A habits, then update the speaking guidance before drafting.

## Required References

Read these files before producing a substantial draft or revision:

- `references/corpus-coverage.md`: source coverage for the 27 supplied titles; distinguishes local PDF full text, public PMC HTML full text, and metadata/title-only entries.
- `references/style-profile.md`: corpus-derived style statistics, terminology, rhetorical moves, and drafting implications.
- `references/writing-and-speaking-protocol.md`: workflow for papers, manuscript sections, reviewer responses, and oral presentation scripts.

For a very small request, such as rewriting one sentence, read `references/writing-and-speaking-protocol.md` first and consult `references/style-profile.md` only if terminology or tone is uncertain. When making claims about the source corpus, always check `references/corpus-coverage.md`.

## Workflow

1. Identify the requested output type: manuscript section, abstract, cover letter, response, grant-style summary, slide narration, or talk script.
2. Determine the scientific level: molecular, synaptic, circuit, behavioral, disease, method, structural, or review synthesis.
3. Separate direct findings from inferred mechanisms and speculative implications.
4. Draft or revise with a mechanism-first structure:
   - establish the system or process,
   - define the unresolved gap,
   - introduce the method or model,
   - report key evidence,
   - state a restrained mechanistic contribution.
5. Calibrate certainty:
   - use assertive evidence verbs for measured results,
   - use cautious verbs for interpretation, models, and future implications.
6. Remove decorative or promotional language.
7. Return a polished version plus a brief note explaining the main style changes when useful.

## Output Modes

### Manuscript Drafting

Build a compact, journal-ready section with precise nouns and stable terminology. Prefer direct scientific logic over broad field narration.

### Manuscript Revision

Preserve the user's meaning and data. Improve paragraph order, claim calibration, transitions, and mechanistic clarity. Do not add unsupported findings.

### Reviewer Response

Use a calm, technical, evidence-focused tone. Acknowledge the point, state the change or rationale, and quote only the user's supplied manuscript text when needed.

### Oral Presentation / Speaking

Convert paper logic into a concise spoken arc: problem, mechanism, evidence. Because the current corpus is mainly written papers, treat this as an inferred academic presentation voice unless the user supplies actual speech transcripts. For substantial reports, follow the detailed speaking protocol in `references/writing-and-speaking-protocol.md`.

## Corpus Refresh

If the user adds new Sun Jianyuan PDFs or asks to update the style profile, run:

```bash
python scripts/build_style_profile.py <article_dir> --include-public-html --output references/style-profile.md --coverage-output references/corpus-coverage.md
```

Use the bundled Python runtime with `pdfplumber` and `pypdf` when available. The script reads local PDFs first, then optionally queries Europe PMC/PMC for public HTML sources when `--include-public-html` is set. It emits aggregate style observations and avoids long verbatim excerpts.

## Quality Checks

Before finalizing:

- Verify every causal or mechanistic claim is supported by the user's data or phrased as inference.
- Keep technical terminology stable.
- Prefer restrained contribution language over inflated impact language.
- Avoid copying source-paper wording beyond short generic scientific phrases.
- For Chinese input, translate the scientific logic first, then revise into the target English style.
