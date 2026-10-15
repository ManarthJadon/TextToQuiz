import io

import pytest
from docx import Document
from pptx import Presentation

from app.extract import extract_text

TEXT = "The sun is a star at the center of our solar system. " * 2


def make_docx(text):
    buf = io.BytesIO()
    doc = Document()
    doc.add_paragraph(text)
    doc.save(buf)
    return buf.getvalue()


def make_pptx(text):
    buf = io.BytesIO()
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    slide.shapes.title.text = text
    prs.save(buf)
    return buf.getvalue()


def test_extract_txt_and_md():
    assert extract_text("a.txt", b"hello") == "hello"
    assert extract_text("a.MD", b"# hi") == "# hi"


def test_extract_docx():
    assert "sun" in extract_text("a.docx", make_docx(TEXT))


def test_extract_pptx():
    assert "sun" in extract_text("a.pptx", make_pptx(TEXT))


def test_extract_docx_includes_tables():
    buf = io.BytesIO()
    doc = Document()
    doc.add_paragraph("before")
    doc.add_table(rows=1, cols=2).cell(0, 0).text = "Q1 what is x"
    doc.save(buf)
    assert "Q1 what is x" in extract_text("a.docx", buf.getvalue())


def test_extract_unsupported_type():
    with pytest.raises(ValueError):
        extract_text("a.exe", b"x")
