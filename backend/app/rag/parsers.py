# coding=utf-8
"""Document parsers: bytes -> markdown/plain text (port of MaxKB split handles).

Mirrors ``apps/common/handle/impl/text/*_split_handle.py``:
  * plain text / markdown -> decode
  * PDF  -> pypdf (font-size heading detection -> markdown)
  * HTML -> BeautifulSoup + markdownify
  * DOCX -> python-docx (paragraphs + tables -> markdown)
  * XLSX -> openpyxl (each sheet -> markdown table)
  * CSV  -> markdown table
  * ZIP  -> recursive extraction of the contained files

Each parser returns a list of ``ParsedDocument`` so multi-sheet / multi-file
archives map onto the same upstream ``Document`` (as the legacy serializer did).
Images inside DOCX are intentionally skipped (would require OSS File storage);
text content is preserved.
"""
from __future__ import annotations

import csv
import io
import os
import re
import zipfile
from dataclasses import dataclass
from typing import List

from charset_normalizer import detect


@dataclass
class ParsedDocument:
    name: str
    content: str


_IMAGE_EXT = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg", ".ico")
_VIDEO_EXT = (".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv", ".webm", ".mpg", ".mpeg", ".3gp", ".ts", ".rmvb")
_AUDIO_EXT = (".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma", ".opus", ".alac", ".aiff", ".amr")


def _decode(buf: bytes) -> str:
    enc = detect(buf).get("encoding") or "utf-8"
    try:
        return buf.decode(enc)
    except (LookupError, UnicodeDecodeError):
        return buf.decode("utf-8", errors="ignore")


# --------------------------------------------------------------------------- PDF
def _pdf_to_markdown(content: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(content))
    font_sizes: List[float] = []
    page_lines: List[List[tuple]] = []
    for page in reader.pages:
        lines = _pdf_extract_page_lines(page)
        page_lines.append(lines)
        for _text, size in lines:
            if _text and size > 0:
                font_sizes.append(size)
    if not font_sizes:
        body_size = 12.0
    else:
        from collections import Counter

        body_size = Counter(font_sizes).most_common(1)[0][0]

    md: List[str] = []
    for page_num, page in enumerate(reader.pages):
        for text, size in page_lines[page_num]:
            if not text:
                continue
            diff = size - body_size
            if diff > 2:
                md.append(f"## {text}\n\n")
            elif diff > 0.5:
                md.append(f"### {text}\n\n")
            else:
                md.append(f"{text}\n")
        md.append("\n")
    return "".join(md).replace("\0", "")


def _pdf_extract_page_lines(page):
    lines: List[tuple] = []
    current_text: List[str] = []
    current_sizes: List[float] = []

    def flush():
        text = "".join(current_text).strip()
        if text:
            lines.append((text, current_sizes[0] if current_sizes else 0))
        current_text.clear()
        current_sizes.clear()

    def visitor(text, cm, tm, font_dict, font_size):
        if text is None:
            return
        parts = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        for idx, part in enumerate(parts):
            current_text.append(part)
            if part.strip() and font_size:
                current_sizes.append(float(font_size))
            if idx < len(parts) - 1:
                flush()

    try:
        page.extract_text(visitor_text=visitor)
    except Exception:
        text = page.extract_text() or ""
        return [(ln.strip(), 0) for ln in text.splitlines() if ln.strip()]
    flush()
    if lines:
        return lines
    text = page.extract_text() or ""
    return [(ln.strip(), 0) for ln in text.splitlines() if ln.strip()]


# -------------------------------------------------------------------------- HTML
def _html_to_markdown(content: bytes) -> str:
    from bs4 import BeautifulSoup
    from markdownify import markdownify

    buf = content
    soup = BeautifulSoup(buf, "html.parser")
    meta = [m.attrs.get("charset") for m in soup.find_all("meta") if m.attrs and "charset" in m.attrs]
    enc = meta[0] if meta else detect(buf).get("encoding") or "utf-8"
    try:
        text = buf.decode(enc)
    except (LookupError, UnicodeDecodeError):
        text = buf.decode("utf-8", errors="ignore")
    # drop anchor-only links so markdownify keeps readable text
    for a in soup.find_all("a", href=re.compile(r"^#")):
        a.unwrap()
    return markdownify(str(soup), heading_style="ATX")


# -------------------------------------------------------------------------- DOCX
def _docx_to_markdown(content: bytes) -> str:
    from docx import Document as DocxDocument
    from docx.oxml.ns import qn
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    doc = DocxDocument(io.BytesIO(content))
    out: List[str] = []

    def title_level(p: Paragraph):
        try:
            if p.style and p.style.name:
                name = p.style.name
                if name.startswith("Heading") or name.startswith("标题"):
                    digits = "".join(ch for ch in name if ch.isdigit())
                    if digits:
                        return int(digits)
        except Exception:
            pass
        return None

    def cell_text(cell) -> str:
        return " ".join(par.text for par in cell.paragraphs).replace("\n", "</br>")

    for element in doc.element.body:
        tag = str(element.tag)
        if tag.endswith("tbl"):
            table = Table(element, doc)
            rows = table.rows
            if not rows:
                continue
            header = rows[0]
            out.append("| " + " | ".join(cell_text(c) for c in header.cells) + " |")
            out.append("| " + " | ".join("---" for _ in header.cells) + " |")
            for row in rows[1:]:
                out.append("| " + " | ".join(cell_text(c) for c in row.cells) + " |")
            out.append("")
        elif tag.endswith("p"):
            p = Paragraph(element, doc)
            level = title_level(p)
            txt = p.text
            if level is not None and txt:
                out.append("#" * level + " " + txt)
            elif txt:
                out.append(txt)
            out.append("")
    # qn imported for parity with legacy handler; referenced to avoid unused import
    _ = qn
    return "\n".join(out)


# ------------------------------------------------------------------------- XLSX
def _xlsx_to_markdown(content: bytes) -> List[ParsedDocument]:
    import openpyxl

    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    docs: List[ParsedDocument] = []
    for sheet in wb.worksheets:
        rows = list(sheet.iter_rows(values_only=True))
        if not rows:
            continue
        header = rows[0]
        lines = ["| " + " | ".join("" if c is None else str(c) for c in header) + " |"]
        lines.append("| " + " | ".join("---" for _ in header) + " |")
        for row in rows[1:]:
            lines.append("| " + " | ".join("" if c is None else str(c).replace("\n", "<br>") for c in row) + " |")
        docs.append(ParsedDocument(name=sheet.title, content="\n".join(lines)))
    return docs


# -------------------------------------------------------------------------- CSV
def _csv_to_markdown(content: bytes) -> ParsedDocument:
    text = _decode(content)
    reader = csv.reader(io.StringIO(text))
    rows = [r for r in reader]
    if not rows:
        return ParsedDocument(name="", content="")
    header = rows[0]
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join("---" for _ in header) + " |"]
    for row in rows[1:]:
        lines.append("| " + " | ".join(row) + " |")
    return ParsedDocument(name="", content="\n".join(lines))


# -------------------------------------------------------------------------- ZIP
def _zip_to_markdown(content: bytes) -> List[ParsedDocument]:
    docs: List[ParsedDocument] = []
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        for name in zf.namelist():
            if name.endswith("/"):
                continue
            lower = name.lower()
            if lower.endswith(_IMAGE_EXT + _VIDEO_EXT + _AUDIO_EXT):
                continue
            try:
                data = zf.read(name)
            except Exception:
                continue
            docs.extend(parse_file(os.path.basename(name), data))
    return docs


# --------------------------------------------------------------------- dispatch
def parse_file(filename: str, content: bytes) -> List[ParsedDocument]:
    """Parse ``content`` (raw bytes) into one or more ``ParsedDocument``."""
    lower = filename.lower()
    if lower.endswith((".md", ".txt", ".text")):
        return [ParsedDocument(name=filename, content=_decode(content))]
    if lower.endswith((".pdf", ".PDF")):
        return [ParsedDocument(name=filename, content=_pdf_to_markdown(content))]
    if lower.endswith((".html", ".htm")):
        return [ParsedDocument(name=filename, content=_html_to_markdown(content))]
    if lower.endswith((".docx", ".doc")):
        return [ParsedDocument(name=filename, content=_docx_to_markdown(content))]
    if lower.endswith((".xlsx",)):
        return _xlsx_to_markdown(content)
    if lower.endswith((".csv", ".tsv")):
        return [_csv_to_markdown(content)]
    if lower.endswith((".zip",)):
        return _zip_to_markdown(content)
    # best-effort: try to decode as text
    return [ParsedDocument(name=filename, content=_decode(content))]
