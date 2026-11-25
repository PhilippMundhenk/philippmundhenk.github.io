#!/usr/bin/env python3
"""Render files/library.bib as static HTML for the publications page.

Usage: python3 tools/bib2publications.py [files/library.bib] [_includes]

Writes _includes/publications.html (everything except patents) and _includes/patents.html.

Standard library only. The output is a plain HTML fragment (no scripts), grouped by year,
newest first. The Pages workflow runs this before every build; run it locally after editing
the .bib file to preview the result.
"""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

OWN_NAME = "Philipp Mundhenk"
LABELS = {
    "article": "Journal",
    "inproceedings": "Conference",
    "conference": "Conference",
    "phdthesis": "PhD thesis",
    "mastersthesis": "Thesis",
    "patent": "Patent",
    "book": "Book",
    "inbook": "Book chapter",
    "incollection": "Book chapter",
    "techreport": "Technical report",
    "misc": "Misc",
}


def parse_bib(text: str) -> list[dict]:
    """Minimal BibTeX parser: @type{key, field = {value} | "value" | bare, ...}."""
    entries = []
    pos = 0
    while True:
        m = re.compile(r"@\s*(\w+)\s*\{\s*([^,\s]*)\s*,", re.S).search(text, pos)
        if not m:
            break
        entry = {"entrytype": m.group(1).lower(), "key": m.group(2)}
        i = m.end()
        while i < len(text):
            fm = re.compile(r"\s*(\w+)\s*=\s*", re.S).match(text, i)
            if not fm:
                close = text.find("}", i)
                i = close + 1 if close >= 0 else len(text)
                break
            name = fm.group(1).lower()
            i = fm.end()
            if text[i] == "{":
                depth, start = 0, i
                while i < len(text):
                    if text[i] == "{":
                        depth += 1
                    elif text[i] == "}":
                        depth -= 1
                        if depth == 0:
                            break
                    i += 1
                value = text[start + 1:i]
                i += 1
            elif text[i] == '"':
                end = text.index('"', i + 1)
                value = text[i + 1:end]
                i = end + 1
            else:
                vm = re.compile(r"[^,}\s]+").match(text, i)
                value = vm.group(0)
                i = vm.end()
            entry[name] = clean(value)
            sep = re.compile(r"\s*,?").match(text, i)
            i = sep.end()
            if re.compile(r"\s*\}").match(text, i):
                i = re.compile(r"\s*\}").match(text, i).end()
                break
        entries.append(entry)
        pos = i
    return entries


def clean(value: str) -> str:
    value = value.replace("{\\&}", "&").replace("\\&", "&").replace("--", "–")
    value = value.replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", value).strip()


def e(text: str) -> str:
    return html.escape(text, quote=True)


def authors(entry: dict) -> str:
    names = [a.strip() for a in entry.get("author", "").split(" and ") if a.strip()]
    out = []
    for name in names:
        if "," in name:  # "Last, First" -> "First Last"
            last, first = [p.strip() for p in name.split(",", 1)]
            name = f"{first} {last}"
        if name in (OWN_NAME, "Mundhenk Philipp"):
            out.append(f"<strong>{e(OWN_NAME)}</strong>")
        else:
            out.append(e(name))
    return ", ".join(out)


def venue(entry: dict) -> str:
    t = entry["entrytype"]
    parts = []
    if t in ("inproceedings", "conference"):
        parts.append(f"In: <em>{e(entry.get('booktitle', ''))}</em>")
        if entry.get("location") and entry["location"].split()[0].strip(",") not in entry.get("booktitle", ""):
            parts.append(e(entry["location"]))
        if entry.get("pages"):
            parts.append(f"pp. {e(entry['pages'])}")
    elif t == "article":
        journal = e(entry.get("journal", ""))
        vol = entry.get("volume", "")
        num = f"({entry['number']})" if entry.get("number") else ""
        parts.append(f"<em>{journal}</em>" + (f", {e(vol)}{e(num)}" if vol else ""))
        if entry.get("pages"):
            parts.append(f"pp. {e(entry['pages'])}")
    elif t in ("phdthesis", "mastersthesis"):
        parts.append(e(entry.get("school", "")))
        if entry.get("publisher"):
            parts.append(e(entry["publisher"]))
        if entry.get("isbn"):
            parts.append(f"ISBN {e(entry['isbn'])}")
    elif t == "patent":
        parts.append(e(entry.get("number") or entry.get("note", "")))
        if entry.get("location"):
            parts.append(e(entry["location"]))
        if entry.get("type") and entry["type"].lower() != "unknown":
            parts.append(e(entry["type"]))
    else:
        for f in ("howpublished", "note"):
            if entry.get(f):
                parts.append(e(entry[f]))
    return ", ".join(p for p in parts if p)


def links(entry: dict) -> str:
    out = []
    doi = entry.get("doi", "")
    if doi:
        out.append(f'DOI: <a href="https://doi.org/{e(doi)}">{e(doi)}</a>')
    url = entry.get("url", "")
    if url and not (doi and doi in url):
        label = "PDF" if url.lower().endswith(".pdf") else "Link"
        out.append(f'<a href="{e(url)}">{label}</a>')
    return " · ".join(out)


def render(entries: list[dict], show_type: bool = True, bib_link: bool = True) -> str:
    years: dict[str, list[dict]] = {}
    for entry in entries:
        years.setdefault(entry.get("year", "n.d."), []).append(entry)
    lines = ["<!-- Generated by tools/bib2publications.py from files/library.bib. Do not edit by hand. -->",
             '<div class="publications">']
    for year in sorted(years, reverse=True):
        lines.append(f"<h3>{e(year)}</h3>")
        lines.append("<ul>")
        for entry in years[year]:
            label = LABELS.get(entry["entrytype"], entry["entrytype"].capitalize())
            text = f'{authors(entry)}: "{e(entry.get("title", ""))}".'
            v = venue(entry)
            if v:
                text += f" {v}."
            link = links(entry)
            if link:
                text += f" {link}"
            badge = f'<span class="pubtype">{e(label)}</span> ' if show_type else ""
            lines.append(f'  <li>{badge}{text}</li>')
        lines.append("</ul>")
    if bib_link:
        lines.append('<p>All entries as BibTeX: <a href="/files/library.bib">library.bib</a></p>')
    lines.append("</div>")
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    src = Path(argv[1] if len(argv) > 1 else "files/library.bib")
    out = Path(argv[2] if len(argv) > 2 else "_includes")
    entries = parse_bib(src.read_text(encoding="utf-8"))
    papers = [x for x in entries if x["entrytype"] != "patent"]
    patents = [x for x in entries if x["entrytype"] == "patent"]
    (out / "publications.html").write_text(render(papers), encoding="utf-8")
    (out / "patents.html").write_text(render(patents, show_type=False, bib_link=False), encoding="utf-8")
    print(f"{len(papers)} publications, {len(patents)} patents -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
