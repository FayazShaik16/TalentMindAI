import pytest
import io
import zipfile
from unittest.mock import MagicMock, patch
from httpx import AsyncClient

from app.utils.document_parser import parse_pdf, parse_docx, parse_document

def create_mock_docx(paragraphs: list[str]) -> bytes:
    xml_content = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">\n'
        '<w:body>\n'
    )
    for p in paragraphs:
        xml_content += f'<w:p><w:r><w:t>{p}</w:t></w:r></w:p>\n'
    xml_content += '</w:body>\n</w:document>'
    
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("word/document.xml", xml_content)
    return buf.getvalue()

def test_parse_docx_success():
    docx_bytes = create_mock_docx(["Software Engineer Position", "Required skills: Python, SQL"])
    text = parse_docx(docx_bytes)
    assert "Software Engineer Position" in text
    assert "Required skills: Python, SQL" in text

def test_parse_docx_missing_document_xml():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("other_file.xml", "<xml></xml>")
    docx_bytes = buf.getvalue()
    
    with pytest.raises(ValueError) as exc:
        parse_docx(docx_bytes)
    assert "word/document.xml missing" in str(exc.value)

@patch("pypdf.PdfReader")
def test_parse_pdf_success(mock_pdf_reader_cls):
    mock_reader = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Extracted text from PDF page 1."
    mock_reader.pages = [mock_page]
    mock_pdf_reader_cls.return_value = mock_reader
    
    text = parse_pdf(b"%PDF-1.4...")
    assert text == "Extracted text from PDF page 1."
    mock_pdf_reader_cls.assert_called_once()

def test_parse_document_dispatch():
    docx_bytes = create_mock_docx(["Word doc content"])
    text_docx = parse_document("test.docx", docx_bytes)
    assert text_docx == "Word doc content"
    
    plaintext = parse_document("test.txt", b"Plaintext content")
    assert plaintext == "Plaintext content"

@pytest.mark.anyio
async def test_parse_file_endpoint_docx(client: AsyncClient):
    docx_bytes = create_mock_docx(["Job Title: React Developer", "Experience: 3+ years"])
    files = {
        "file": (
            "job.docx", 
            docx_bytes, 
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    }
    
    response = await client.post("/jobs/parse-file", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "React Developer" in data["data"]["text"]
    assert "3+ years" in data["data"]["text"]

@pytest.mark.anyio
@patch("pypdf.PdfReader")
async def test_parse_file_endpoint_pdf(mock_pdf_reader_cls, client: AsyncClient):
    mock_reader = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Job Title: PDF Developer"
    mock_reader.pages = [mock_page]
    mock_pdf_reader_cls.return_value = mock_reader
    
    files = {
        "file": (
            "job.pdf", 
            b"%PDF-1.4...", 
            "application/pdf"
        )
    }
    
    response = await client.post("/jobs/parse-file", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "PDF Developer" in data["data"]["text"]
