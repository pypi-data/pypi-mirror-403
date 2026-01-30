import PyPDF2


class Extractor:
    def is_extractable(self, path) -> bool:
        pass

    def extract(self, path: str) -> str:
        pass


class PdfExtractor(Extractor):
    def is_extractable(self, path: str) -> bool:
        return path.endswith(".pdf")

    def extract(self, path: str) -> str:
        return "".join(extract_pdf_text(path))


def extract_pdf_text(pdf_path: str) -> list[str]:
    """Извлекает текст из PDF файла"""
    with open(pdf_path, "rb") as file:
        pdf_reader = PyPDF2.PdfReader(file)
        pages_text = []
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text = page.extract_text()
            pages_text.append(text)
    return pages_text
