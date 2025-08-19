import os
import fitz  # pymupdf

def extract_all_docs():
    docs = get_documents(directory = '.\\embeddings\\medcare\\documents\\')
    texts = extract_pdf_files(files = docs)
    return texts


def extract_text(*, pdf_file_name):
    doc = fitz.open(pdf_file_name)
    toc = doc.get_toc()  # Returns list of [level, title, page_number]

    full_text_with_sections = ""
    for page_num, page in enumerate(doc):
        # Add any TOC entries that start on this page
        page_toc_items = [item for item in toc if item[2] == page_num + 1]
        for level, title, page in page_toc_items:
            full_text_with_sections += f"\n{'#' * level} {title}\n"
    
        full_text_with_sections += page.get_text()
    return full_text_with_sections


def extract_pdf_files(*, files):
    texts = [extract_text(pdf_file_name = file) for file in files]
    return texts

def get_documents(*, directory):
    docs = []
    for entry in os.scandir(directory):
        if entry.is_file() and entry.name[-3:] == 'pdf':
            docs.append(directory + entry.name)
    return docs

if __name__ == '__main__':
    extract_all_docs()
