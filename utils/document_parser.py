from PyPDF2 import PdfReader
from pptx import Presentation


def parse_pdf(file) -> str:
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text.strip()


def parse_pptx(file) -> str:
    prs = Presentation(file)
    text = ""
    for slide_num, slide in enumerate(prs.slides, 1):
        text += f"\n--- Slide {slide_num} ---\n"
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                text += shape.text + "\n"
    return text.strip()


def parse_document(uploaded_file) -> str:
    name = uploaded_file.name.lower()
    if name.endswith(".pdf"):
        return parse_pdf(uploaded_file)
    elif name.endswith((".pptx", ".ppt")):
        return parse_pptx(uploaded_file)
    elif name.endswith((".txt", ".md", ".csv")):
        return uploaded_file.read().decode("utf-8")
    else:
        return uploaded_file.read().decode("utf-8", errors="ignore")
