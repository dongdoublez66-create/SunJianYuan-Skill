#!/usr/bin/env python3
"""Build a compact writing-style profile from Sun Jianyuan article sources.

The script distinguishes evidence tiers:
- target PDF full text, when a PDF was downloaded locally;
- target public PMC HTML full text, when no PDF is local but PMC has a page;
- target abstract/title metadata, when full text is not available;
- auxiliary additional PDFs, when present.

It intentionally emits aggregate observations rather than long verbatim source
passages, so the resulting skill guides style without copying papers.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import time
from collections import Counter
from html import unescape
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


USER_AGENT = "Mozilla/5.0 (compatible; CodexStyleProfile/1.1; mailto:research@example.com)"

DOMAIN_TERMS = [
    "synapse",
    "synaptic",
    "vesicle",
    "neurotransmitter",
    "release",
    "endocytosis",
    "exocytosis",
    "calyx",
    "calcium",
    "ca2",
    "channel",
    "neuron",
    "neuronal",
    "transmission",
    "presynaptic",
    "postsynaptic",
    "sensor",
    "structural",
    "mechanism",
    "modulation",
    "pathway",
    "circuit",
    "excitatory",
    "appetite",
    "pain",
]

HEDGES = [
    "may",
    "might",
    "could",
    "likely",
    "possibly",
    "suggest",
    "suggests",
    "suggesting",
    "indicate",
    "indicates",
    "indicating",
    "potential",
    "putative",
    "appears",
]

ASSERTIVE_VERBS = [
    "show",
    "shows",
    "shown",
    "demonstrate",
    "demonstrates",
    "demonstrated",
    "reveal",
    "reveals",
    "revealed",
    "identify",
    "identifies",
    "identified",
    "provide",
    "provides",
    "provided",
    "establish",
    "establishes",
    "support",
    "supports",
]

MOVE_PATTERNS = {
    "knowledge gap": [
        r"remain[s]? unclear",
        r"poorly understood",
        r"not fully understood",
        r"controversial",
        r"unknown",
    ],
    "study announcement": [
        r"\bhere\b",
        r"\bin this study\b",
        r"\bwe investigated\b",
        r"\bwe examined\b",
        r"\bwe analyzed\b",
    ],
    "mechanistic explanation": [
        r"\bmechanism",
        r"\bpathway",
        r"\bunderlying",
        r"\bmediated by\b",
        r"\bvia\b",
    ],
    "evidence synthesis": [
        r"\btogether\b",
        r"\bcollectively\b",
        r"\bour results\b",
        r"\bour findings\b",
        r"\bthese results\b",
    ],
    "significance claim": [
        r"\bprovide[s]? insight",
        r"\badvance[s]?",
        r"\bimportant",
        r"\bcritical",
        r"\bcrucial",
    ],
}


def request_bytes(url: str, accept: str = "*/*", timeout: int = 45) -> bytes:
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
    with urlopen(req, timeout=timeout) as response:
        return response.read()


def request_json(url: str) -> dict:
    for attempt in range(3):
        try:
            return json.loads(request_bytes(url, "application/json").decode("utf-8", errors="replace"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
            time.sleep(0.7 + attempt)
    return {}


def query_europe_pmc(doi: str) -> dict:
    if not doi:
        return {}
    query = quote(f'DOI:"{doi}"')
    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={query}&format=json&pageSize=1"
    data = request_json(url)
    results = data.get("resultList", {}).get("result", []) if data else []
    return results[0] if results else {}


def read_pdf_text(path: Path) -> str:
    try:
        import pdfplumber

        chunks: list[str] = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                chunks.append(page.extract_text(x_tolerance=1, y_tolerance=3) or "")
        text = "\n".join(chunks)
        if text.strip():
            return text
    except Exception:
        pass

    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        return ""


def strip_html(html: str) -> str:
    html = re.sub(r"(?is)<script.*?</script>", " ", html)
    html = re.sub(r"(?is)<style.*?</style>", " ", html)
    html = re.sub(r"(?is)<nav.*?</nav>", " ", html)
    html = re.sub(r"(?is)<header.*?</header>", " ", html)
    html = re.sub(r"(?is)<footer.*?</footer>", " ", html)
    main = re.search(r"(?is)<main[^>]*>(.*?)</main>", html)
    if main:
        html = main.group(1)
    html = re.sub(r"<[^>]+>", " ", html)
    text = unescape(html)
    text = re.sub(r"\s+", " ", text)
    for marker in [" References ", " Bibliography ", " Supplementary Material ", " Footnotes "]:
        idx = text.find(marker)
        if idx > 4000:
            text = text[:idx]
            break
    return text.strip()


def read_pmc_html_text(pmcid: str) -> str:
    if not pmcid:
        return ""
    url = f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/"
    try:
        html = request_bytes(url, "text/html,application/xhtml+xml,*/*;q=0.8").decode(
            "utf-8", errors="replace"
        )
    except (HTTPError, URLError, TimeoutError):
        return ""
    text = strip_html(html)
    if len(words(text)) < 500:
        return ""
    return text


def clean_text(text: str) -> str:
    text = text.replace("\u00ad", "")
    text = re.sub(r"-\s*\n\s*", "", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_sentences(text: str) -> list[str]:
    candidates = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9(])", text)
    sentences: list[str] = []
    for sentence in candidates:
        sentence = sentence.strip()
        tokens = re.findall(r"[A-Za-z0-9+\-]+", sentence)
        if 6 <= len(tokens) <= 80:
            sentences.append(sentence)
    return sentences


def words(text: str) -> list[str]:
    return [w.lower() for w in re.findall(r"[A-Za-z][A-Za-z0-9+\-]*", text)]


def sentence_stats(sentences: list[str]) -> dict[str, float]:
    lengths = [len(words(s)) for s in sentences]
    if not lengths:
        return {"mean": 0, "median": 0, "p90": 0}
    lengths_sorted = sorted(lengths)
    median = lengths_sorted[len(lengths_sorted) // 2]
    p90 = lengths_sorted[min(len(lengths_sorted) - 1, math.floor(len(lengths_sorted) * 0.9))]
    return {"mean": sum(lengths) / len(lengths), "median": float(median), "p90": float(p90)}


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def row_title(row: dict[str, str], fallback: str = "") -> str:
    title = row.get("found_title") or row.get("target_title") or row.get("title") or fallback
    title = re.sub(r"<[^>]+>", "", unescape(title))
    return re.sub(r"\s+", " ", title).strip()


def row_year(row: dict[str, str]) -> str:
    return row.get("found_year") or row.get("target_year") or row.get("year") or ""


def row_journal(row: dict[str, str]) -> str:
    return row.get("found_journal") or row.get("target_journal") or row.get("journal") or ""


def analyze_text(text: str, counters: dict[str, Counter], all_sentences: list[str], all_words: list[str]) -> tuple[int, int]:
    text = clean_text(text)
    sentences = split_sentences(text)
    tokens = words(text)
    lowered = " ".join(tokens)
    all_sentences.extend(sentences)
    all_words.extend(tokens)

    token_counts = Counter(tokens)
    for term in DOMAIN_TERMS:
        count = lowered.count(term)
        if count:
            counters["terms"][term] += count
    for term in HEDGES:
        counters["hedges"][term] += token_counts[term]
    for term in ASSERTIVE_VERBS:
        counters["assertive"][term] += token_counts[term]
    for move, patterns in MOVE_PATTERNS.items():
        for pattern in patterns:
            counters["moves"][move] += len(re.findall(pattern, text, flags=re.I))
    return len(sentences), len(tokens)


def build_sources(pdf_dir: Path, include_public_html: bool) -> tuple[list[dict[str, object]], list[dict[str, str]]]:
    target_rows = load_csv(pdf_dir / "metadata.csv")
    additional_rows = load_csv(pdf_dir / "additional_candidates.csv")
    sources: list[dict[str, object]] = []
    coverage: list[dict[str, str]] = []

    for row in target_rows:
        pdf_file = row.get("pdf_file", "")
        pdf_path = pdf_dir / pdf_file if pdf_file else None
        title = row_title(row)
        info = query_europe_pmc(row.get("doi", "")) if include_public_html else {}
        pmcid = info.get("pmcid", "")
        abstract = clean_text(info.get("abstractText", ""))
        tier = "metadata/title only"
        text = title
        source_path = ""

        if pdf_path and pdf_path.exists():
            text = read_pdf_text(pdf_path)
            tier = "target PDF full text"
            source_path = pdf_file
        elif include_public_html and pmcid:
            html_text = read_pmc_html_text(pmcid)
            if html_text:
                text = html_text
                tier = "target public PMC HTML full text"
                source_path = f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/"
            elif abstract:
                text = f"{title}. {abstract}"
                tier = "target abstract/title only"
                source_path = f"Europe PMC {pmcid}"
        elif abstract:
            text = f"{title}. {abstract}"
            tier = "target abstract/title only"
            source_path = "Europe PMC"

        sources.append({"row": row, "text": text, "tier": tier, "auxiliary": False, "source_path": source_path})
        coverage.append(
            {
                "index": row.get("index", ""),
                "year": row_year(row),
                "journal": row_journal(row),
                "title": title,
                "doi": row.get("doi", ""),
                "tier": tier,
                "pmcid": pmcid,
                "source": source_path,
            }
        )
        if include_public_html:
            time.sleep(0.15)

    for row in additional_rows:
        pdf_file = row.get("pdf_file", "")
        pdf_path = pdf_dir / pdf_file if pdf_file else None
        if not pdf_path or not pdf_path.exists():
            continue
        sources.append(
            {
                "row": row,
                "text": read_pdf_text(pdf_path),
                "tier": "auxiliary PDF full text",
                "auxiliary": True,
                "source_path": pdf_file,
            }
        )

    return sources, coverage


def analyze(pdf_dir: Path, include_public_html: bool) -> dict[str, object]:
    counters = {
        "terms": Counter(),
        "hedges": Counter(),
        "assertive": Counter(),
        "moves": Counter(),
    }
    all_sentences: list[str] = []
    all_words: list[str] = []
    documents = []
    sources, coverage = build_sources(pdf_dir, include_public_html)

    for source in sources:
        sentence_count, word_count = analyze_text(
            str(source["text"]), counters, all_sentences, all_words
        )
        row = source["row"]
        documents.append(
            {
                "title": row_title(row, str(source["source_path"])),
                "journal": row_journal(row),
                "year": row_year(row),
                "tier": source["tier"],
                "auxiliary": source["auxiliary"],
                "sentences": sentence_count,
                "words": word_count,
            }
        )

    sentence_openers = Counter()
    for sentence in all_sentences:
        first_words = words(sentence)[:3]
        if len(first_words) >= 2:
            opener = " ".join(first_words[:2])
            if opener not in {"the present", "this article", "in the"}:
                sentence_openers[opener] += 1

    tier_counts = Counter(doc["tier"] for doc in documents if not doc["auxiliary"])
    return {
        "documents": documents,
        "coverage": coverage,
        "target_count": len(coverage),
        "target_full_text_count": sum(1 for doc in documents if not doc["auxiliary"] and "full text" in doc["tier"]),
        "auxiliary_full_text_count": sum(1 for doc in documents if doc["auxiliary"]),
        "tier_counts": tier_counts,
        "document_count": len(documents),
        "word_count": len(all_words),
        "sentence_count": len(all_sentences),
        "sentence_stats": sentence_stats(all_sentences),
        "term_counts": counters["terms"].most_common(30),
        "hedge_counts": counters["hedges"].most_common(15),
        "assertive_counts": counters["assertive"].most_common(15),
        "move_counts": counters["moves"].most_common(),
        "sentence_openers": sentence_openers.most_common(20),
    }


def render_markdown(results: dict[str, object]) -> str:
    stats = results["sentence_stats"]
    tier_counts = results["tier_counts"]
    lines = [
        "# Sun Jianyuan Style Profile",
        "",
        "This note records what can be learned from the current corpus. It keeps the focus on patterns rather than excerpts: terms that recur, moves that organize the argument, and the level of caution used when moving from data to mechanism.",
        "",
        "## Corpus Coverage",
        "",
        f"- Supplied target titles covered in metadata: {results['target_count']}/27",
        f"- Target full-text sources analyzed: {results['target_full_text_count']}/27",
        f"- Auxiliary full-text PDFs analyzed: {results['auxiliary_full_text_count']}",
        f"- Target PDF full text: {tier_counts.get('target PDF full text', 0)}",
        f"- Target public PMC HTML full text: {tier_counts.get('target public PMC HTML full text', 0)}",
        f"- Target abstract/title only: {tier_counts.get('target abstract/title only', 0)}",
        f"- Target metadata/title only: {tier_counts.get('metadata/title only', 0)}",
        "",
        "Check `references/corpus-coverage.md` before treating any pattern here as if it came from all 27 full texts.",
        "",
        "## Text Statistics",
        "",
        f"- Sources analyzed: {results['document_count']}",
        f"- Approximate words extracted: {results['word_count']}",
        f"- Sentences analyzed: {results['sentence_count']}",
        f"- Sentence length: mean {stats['mean']:.1f} words, median {stats['median']:.0f}, p90 {stats['p90']:.0f}",
        "",
        "## Documents And Evidence Level",
        "",
    ]
    for doc in results["documents"]:
        prefix = "Auxiliary" if doc["auxiliary"] else "Target"
        lines.append(
            f"- {prefix}; {doc['tier']}; {doc['year']} {doc['journal']}: {doc['title']}"
        )

    def table(title: str, rows: list[tuple[str, int]]) -> None:
        lines.extend(["", f"## {title}", "", "| Item | Count |", "|---|---:|"])
        for key, count in rows:
            lines.append(f"| {key} | {count} |")

    table("High-Frequency Domain Terms", results["term_counts"])
    table("Rhetorical Move Signals", results["move_counts"])
    table("Hedging And Caution Signals", results["hedge_counts"])
    table("Assertive Evidence Verbs", results["assertive_counts"])
    table("Common Sentence Openers", results["sentence_openers"])

    lines.extend(
        [
            "",
            "## Practical Takeaways",
            "",
            "- Start from the mechanism: name the biological process, identify the unresolved step, and then bring in the experiment.",
            "- Use strong verbs for direct observations, but soften the sentence when the claim becomes a model or interpretation.",
            "- Keep the argument close to synaptic, circuit, channel, release, endocytosis/exocytosis, or structure-function language when the user's science allows it.",
            "- Let transitions do real work: contrast, add evidence, or synthesize before interpreting.",
            "- Prefer technical nouns and analytical verbs over decorative adjectives.",
            "- Preserve uncertainty. A speculative mechanism should not be revised into a proven one.",
            "- Treat title-only entries as background signal, not as equal evidence with full-text papers.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_coverage(results: dict[str, object]) -> str:
    lines = [
        "# Corpus Coverage",
        "",
        "This table is the reality check for the corpus. It shows which of the 27 supplied titles were read as full text and which ones only contributed bibliographic signal.",
        "",
        "| # | Year | Journal | Title | DOI | Evidence Tier | PMCID/Source |",
        "|---:|---|---|---|---|---|---|",
    ]
    for row in results["coverage"]:
        doi = row["doi"]
        doi_cell = f"[{doi}](https://doi.org/{doi})" if doi else ""
        source = row["pmcid"] or row["source"]
        lines.append(
            f"| {row['index']} | {row['year']} | {row['journal']} | {row['title']} | "
            f"{doi_cell} | {row['tier']} | {source} |"
        )
    lines.extend(
        [
            "",
            "Evidence levels:",
            "- `target PDF full text`: local PDF was available and parsed.",
            "- `target public PMC HTML full text`: no local PDF, but a public PMC HTML page was parsed without storing raw text.",
            "- `target abstract/title only`: no full text was available through the public sources checked; only abstract/title-level text informed aggregate signals.",
            "- `metadata/title only`: only bibliographic title metadata was available.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_text(path: Path, text: str) -> None:
    output = path if path.is_absolute() else Path.cwd() / path
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp_output = output.with_name(output.name + ".tmp")
    tmp_output.write_text(text, encoding="utf-8")
    os.replace(tmp_output, output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "article_dir",
        type=Path,
        help="Folder containing metadata.csv, optional additional_candidates.csv, and any downloaded PDFs.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("references/style-profile.md"),
        help="Markdown style profile to write.",
    )
    parser.add_argument(
        "--coverage-output",
        type=Path,
        default=Path("references/corpus-coverage.md"),
        help="Markdown corpus coverage table to write.",
    )
    parser.add_argument(
        "--include-public-html",
        action="store_true",
        help="Query Europe PMC and parse public PMC HTML for target articles that lack local PDFs.",
    )
    args = parser.parse_args()

    results = analyze(args.article_dir, args.include_public_html)
    write_text(args.output, render_markdown(results))
    write_text(args.coverage_output, render_coverage(results))
    print(
        "Wrote "
        f"{args.output} and {args.coverage_output}; "
        f"target full text {results['target_full_text_count']}/27."
    )


if __name__ == "__main__":
    main()
