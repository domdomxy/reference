import os
from whoosh.index import create_in
from whoosh.fields import Schema, TEXT
from PyPDF2 import PdfReader
from docx import Document

DOCUMENTS_DIR = "documents"
INDEX_DIR = "indexdir"

def read_txt(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def read_pdf(path):
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text()
    return text

def read_docx(path):
    doc = Document(path)
    return " ".join(p.text for p in doc.paragraphs)

def create_index():
    if not os.path.exists(INDEX_DIR):
        os.mkdir(INDEX_DIR)

    schema = Schema(
        title=TEXT(stored=True),
        content=TEXT(stored=True)
    )

    ix = create_in(INDEX_DIR, schema)
    writer = ix.writer()

    for filename in os.listdir(DOCUMENTS_DIR):
        path = os.path.join(DOCUMENTS_DIR, filename)

        if filename.endswith(".txt"):
            content = read_txt(path)
        elif filename.endswith(".pdf"):
            content = read_pdf(path)
        elif filename.endswith(".docx"):
            content = read_docx(path)
        else:
            continue

        writer.add_document(
            title=filename,
            content=content
        )

    writer.commit()
    print("✅ Index created successfully")

if __name__ == "__main__":
    create_index()