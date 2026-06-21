---
name: sun-jianyuan-style
description: Help draft, revise, or diagnose neuroscience and biomedical research writing in a style aligned with Sun Jianyuan's published papers. Use for manuscript abstracts, introductions, results, discussions, cover letters, reviewer responses, grant-like summaries, slide narration, oral reports, and Chinese-to-English academic prose that should sound mechanism-first, data-bound, and scientifically restrained.
---

# Sun Jianyuan Style

## What This Is For

This guide helps shape research text toward the habits that show up repeatedly in Sun Jianyuan's papers: start from the biological mechanism, keep the terminology precise, let the evidence carry the paragraph, and avoid making the conclusion larger than the data.

Keep the authorship with the user. Avoid lifting memorable sentences from the papers. The aim is alignment at the level of structure, judgment, and scientific tone.

## What It Can Know

The corpus behind the current version is mostly written papers. That is enough to infer a paper-like reporting voice, but not enough to recreate someone's real spoken manner. Real speech would need recordings, transcripts, interviews, lectures, lab-meeting notes, or Q&A records.

When asked for a "speaking style", treat it as paper logic translated into an academic oral report unless the user supplies actual speech samples. If speech samples are supplied, first study their openings, transitions, pacing, uncertainty language, figure descriptions, and Q&A habits, then adapt the speaking notes.

## What To Read

For any substantial draft or rewrite, read these in order:

- `references/corpus-coverage.md` for what the corpus actually contains.
- `references/style-profile.md` for the style signals extracted from the papers.
- `references/writing-and-speaking-protocol.md` for practical writing and speaking moves.

For a one-sentence polish, start with `references/writing-and-speaking-protocol.md`; check the profile only if the wording or certainty level is unclear. Whenever you mention the source corpus, check `references/corpus-coverage.md` first.

## Working Method

1. Decide what the user is writing: paper section, abstract, response letter, grant-style paragraph, slide narration, or spoken report.
2. Identify the scientific level: molecule, synapse, circuit, behavior, disease, method, structure, or review.
3. Separate what the data directly show from what the data only suggest.
4. Build the text around a simple path:
   - name the process or system,
   - state the unresolved mechanism,
   - introduce the method or preparation,
   - report the main observation,
   - close with a restrained mechanistic contribution.
5. Use stronger verbs for direct measurements and softer verbs for interpretation.
6. Remove decoration, promotion, and unsupported certainty.

## Common Uses

### Manuscript Drafting

Write compact, journal-ready prose. Keep the background close to the mechanism being tested; avoid broad neuroscience overview unless the section truly needs it.

### Manuscript Revision

Preserve the user's data and meaning. Improve order, transitions, certainty, and mechanistic clarity. Do not invent findings.

### Reviewer Response

Answer calmly and technically. Acknowledge the point, state what changed or why it did not change, and keep the tone focused on evidence.

### Oral Presentation

Turn paper logic into a spoken path: question, preparation, observation, interpretation, next experiment. For longer reports, follow `references/writing-and-speaking-protocol.md`.

## Updating The Corpus Notes

When new Sun Jianyuan PDFs or public article sources are added, refresh the profile with:

```bash
python scripts/build_style_profile.py <article_dir> --include-public-html --output references/style-profile.md --coverage-output references/corpus-coverage.md
```

Use a Python environment with `pdfplumber` and `pypdf` when possible. The script reads local PDFs first, optionally checks Europe PMC/PMC for public HTML, and writes only aggregate notes rather than long source excerpts.

## Final Check

Before returning the draft, make sure:

- causal claims are supported or clearly softened;
- mechanisms and observations are not mixed together;
- terminology stays stable;
- the ending is contribution-focused rather than promotional;
- no distinctive source-paper sentence has been copied.
