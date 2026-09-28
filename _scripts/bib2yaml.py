#!/usr/bin/env python3
"""Convert a BibTeX file to _data/publications.yml for the Cayman publications page.

Usage: python bib2yaml.py peer_reviewed.bib > _data/peer_reviewed.yml
"""
import re
import sys

import bibtexparser
import yaml
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode

ME = ["varas enríquez", "varas enriquez"]      # your surname, lowercase, to bold your name
PDF_DIR = "/assets/papers/"                    # where bare PDF filenames live
FALLBACK_ABBR = {
    "article": "Article", "phdthesis": "Thesis", "mastersthesis": "Thesis",
    "unpublished": "Preprint", "misc": "Preprint", "inbook": "Chapter",
    "incollection": "Chapter", "inproceedings": "Conference", "book": "Book",
}


def clean(s):
    s = re.sub(r"\s+", " ", s or "").strip()
    return s.replace("{", "").replace("}", "")


def fmt_author(a):
    a = clean(a)
    if "," in a:
        last, first = [x.strip() for x in a.split(",", 1)]
    else:
        low = a.lower()
        match = next((m for m in ME if low.endswith(m)), None)
        if match:                                   # "Pablo J. Varas Enríquez"
            last, first = a[-len(match):], a[:-len(match)].strip()
        else:
            parts = a.split()
            last, first = parts[-1], " ".join(parts[:-1])
    initials = " ".join(p[0] + "." for p in re.split(r"[\s\-]+", first) if p)
    name = f"{last}, {initials}".strip(", ")
    if any(m in last.lower() for m in ME):
        name = f"<strong>{name}</strong>"
    return name


def fmt_authors(raw):
    names = [fmt_author(a) for a in re.split(r"\s+and\s+", raw or "") if a.strip()]
    if len(names) <= 1:
        return "".join(names)
    return ", ".join(names[:-1]) + ", and " + names[-1]


def link(value, default_dir=""):
    value = clean(value)
    if not value:
        return None
    if value.startswith(("http://", "https://", "/")):
        return value
    return default_dir + value


parser = BibTexParser(common_strings=True)
parser.customization = convert_to_unicode
with open(sys.argv[1], encoding="utf-8") as f:
    db = bibtexparser.load(f, parser=parser)

out = []
for e in db.entries:
    year = re.sub(r"\D", "", e.get("year", ""))[:4]
    if not year:
        print(f"Skipping {e['ID']}: no year", file=sys.stderr)
        continue
    venue = next((clean(e[k]) for k in
                  ("journal", "booktitle", "school", "publisher", "howpublished", "note")
                  if e.get(k)), "")
    html = link(e.get("html", "")) or link(e.get("url", ""))
    if not html and e.get("doi"):
        html = "https://doi.org/" + clean(e["doi"])
    item = {
        "abbr": clean(e.get("abbr")) or FALLBACK_ABBR.get(e["ENTRYTYPE"], "Other"),
        "year": int(year),
        "title": clean(e.get("title")),
        "authors": fmt_authors(e.get("author")),
        "venue": venue,
        "abstract": clean(e.get("abstract")) or None,
        "html": html,
        "pdf": link(e.get("pdf", ""), PDF_DIR),
        "preprint": link(e.get("preprint", "")),
    }
    out.append({k: v for k, v in item.items() if v})

out.sort(key=lambda x: -x["year"])
yaml.safe_dump(out, sys.stdout, allow_unicode=True, sort_keys=False, width=100000)
