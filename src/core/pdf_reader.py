from PyPDF2 import PdfReader

class PDFReader:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path

    def extract_text_in_pages(self):
        reader = PdfReader(self.pdf_path)
        pages = []
        for idx, page in enumerate(reader.pages, start=1):
            pages.append((idx, page.extract_text()))
        
        return pages