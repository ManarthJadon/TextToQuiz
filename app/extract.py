"""Turns uploaded files (PDF, Word, PowerPoint, text) into plain text."""
import io

from docx import Document
from docx.table import Table
from pptx import Presentation
from pypdf import PdfReader


def table_text(table) -> str:  # works for Word and PowerPoint tables
    return "\n".join(" | ".join(cell.text for cell in row.cells) for row in table.rows)


def extract_text(filename: str, data: bytes) -> str:
    ext = filename.lower().rsplit(".", 1)[-1]
    if ext == "pdf":
        reader = PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if ext == "docx":
        doc = Document(io.BytesIO(data))
        # iter_inner_content keeps paragraphs and tables in document order
        return "\n".join(
            table_text(block) if isinstance(block, Table) else block.text
            for block in doc.iter_inner_content()
        )
    if ext == "pptx":
        prs = Presentation(io.BytesIO(data))
        parts = []
        for slide in prs.slides:
            for shape in slide.shapes:
                if shape.has_text_frame:
                    parts.append(shape.text_frame.text)
                elif shape.has_table:
                    parts.append(table_text(shape.table))
        return "\n".join(parts)
    if ext in ("txt", "md"):
        return data.decode("utf-8", errors="ignore")
    raise ValueError(f"Unsupported file type: .{ext}")
