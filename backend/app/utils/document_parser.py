import io
import zipfile
import xml.etree.ElementTree as ET
import pypdf
from app.core.logging.logging import logger

def parse_pdf(file_bytes: bytes) -> str:
    """
    Extract text from a PDF file using pypdf.
    """
    try:
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        text_content = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_content.append(text)
        return "\n".join(text_content)
    except Exception as e:
        logger.error("parse_pdf_failed", error=str(e))
        raise ValueError(f"Failed to parse PDF document: {str(e)}")

def parse_docx(file_bytes: bytes) -> str:
    """
    Extract text from a DOCX file using standard python libraries (zipfile and xml.etree.ElementTree).
    """
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
            if "word/document.xml" not in z.namelist():
                raise ValueError("Invalid DOCX format: word/document.xml missing.")
            
            doc_xml = z.read("word/document.xml")
            root = ET.fromstring(doc_xml)
            
            # OpenXML Namespace
            w_ns = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            p_tag = f"{{{w_ns}}}p"
            t_tag = f"{{{w_ns}}}t"
            
            paragraphs = []
            for p in root.iter(p_tag):
                p_text = []
                for t in p.iter(t_tag):
                    if t.text:
                        p_text.append(t.text)
                if p_text:
                    paragraphs.append("".join(p_text))
            
            # Namespace-agnostic fallback in case of non-standard schema variations
            if not paragraphs:
                for elem in root.iter():
                    tag_name = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                    if tag_name == "p":
                        p_text = []
                        for child in elem.iter():
                            child_tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                            if child_tag == "t" and child.text:
                                p_text.append(child.text)
                        if p_text:
                            paragraphs.append("".join(p_text))
                            
            return "\n".join(paragraphs)
    except Exception as e:
        logger.error("parse_docx_failed", error=str(e))
        raise ValueError(f"Failed to parse DOCX document: {str(e)}")

def parse_document(filename: str, file_bytes: bytes) -> str:
    """
    Direct document parsing dispatcher based on file extension.
    """
    lower_filename = filename.lower()
    if lower_filename.endswith(".pdf"):
        return parse_pdf(file_bytes)
    elif lower_filename.endswith(".docx"):
        return parse_docx(file_bytes)
    elif lower_filename.endswith(".txt") or lower_filename.endswith(".md"):
        # Decode as utf-8 (with fallback ignore/replace for non-utf8 encodings)
        return file_bytes.decode("utf-8", errors="ignore")
    else:
        # Generic decoding
        try:
            return file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError(f"Unsupported file format for: {filename}")
