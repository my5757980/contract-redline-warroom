"""Contract ingest → clause-addressable sections (Principle V: citations).

Accepts plain text or PDF. Splits on numbered headings like "8.2 Limitation of
Liability" so every finding can cite a real section id + quoted source text.
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass

SECTION_RE = re.compile(r"^\s*(\d+(?:\.\d+)*)\s+([A-Z][^\n]{2,80})", re.MULTILINE)


@dataclass
class Clause:
    id: str
    section: str
    title: str
    text: str

    def cite(self, max_len: int = 160) -> str:
        snippet = " ".join(self.text.split())
        return snippet[:max_len] + ("..." if len(snippet) > max_len else "")


@dataclass
class Contract:
    id: str
    title: str
    raw_text: str
    clauses: list[Clause]

    def section(self, sid: str) -> Clause | None:
        return next((c for c in self.clauses if c.section == sid), None)


def _read_pdf(path: str) -> str:
    from pypdf import PdfReader  # local import so text-only path needs no pypdf
    reader = PdfReader(path)
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def ingest(raw_text: str | None = None, *, path: str | None = None,
           title: str = "Untitled Contract") -> Contract:
    if path and path.lower().endswith(".pdf"):
        raw_text = _read_pdf(path)
    elif path:
        with open(path, "r", encoding="utf-8") as fh:
            raw_text = fh.read()
    if not raw_text:
        raise ValueError("ingest() needs raw_text or a path")

    matches = list(SECTION_RE.finditer(raw_text))
    clauses: list[Clause] = []
    if not matches:
        # no numbered sections → one clause per paragraph
        for i, para in enumerate(p for p in raw_text.split("\n\n") if p.strip()):
            clauses.append(Clause(str(uuid.uuid4()), section=str(i + 1),
                                  title=f"Paragraph {i + 1}", text=para.strip()))
    else:
        for i, m in enumerate(matches):
            start = m.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(raw_text)
            section, head = m.group(1), m.group(2).strip()
            clauses.append(Clause(str(uuid.uuid4()), section=section, title=head,
                                  text=raw_text[start:end].strip()))
    return Contract(id=str(uuid.uuid4()), title=title, raw_text=raw_text, clauses=clauses)
