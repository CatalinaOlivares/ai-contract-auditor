from PyPDF2 import PdfReader
from io import BytesIO
from typing import Optional


class PDFExtractor:
    """Service to extract text from PDF files."""

    def extract_text(self, pdf_content: bytes) -> str:
        """
        Extract text from PDF bytes.

        Args:
            pdf_content: Raw bytes of the PDF file

        Returns:
            Extracted text as string
        """
        try:
            pdf_file = BytesIO(pdf_content)
            reader = PdfReader(pdf_file)

            text_parts = []
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(f"--- Page {page_num + 1} ---\n{page_text}")

            return "\n\n".join(text_parts)
        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")

    def get_page_count(self, pdf_content: bytes) -> int:
        """Get the number of pages in a PDF."""
        try:
            pdf_file = BytesIO(pdf_content)
            reader = PdfReader(pdf_file)
            return len(reader.pages)
        except Exception:
            return 0

    def extract_text_chunked(
        self,
        pdf_content: bytes,
        max_chars_per_chunk: int = 10000
    ) -> list[str]:
        """
        Extract text from PDF in chunks for large documents.

        Args:
            pdf_content: Raw bytes of the PDF file
            max_chars_per_chunk: Maximum characters per chunk

        Returns:
            List of text chunks
        """
        full_text = self.extract_text(pdf_content)

        if len(full_text) <= max_chars_per_chunk:
            return [full_text]

        # Split by pages first
        pages = full_text.split("--- Page ")

        chunks = []
        current_chunk = ""

        for page in pages:
            if not page.strip():
                continue

            page_text = f"--- Page {page}" if not page.startswith("---") else page

            if len(current_chunk) + len(page_text) <= max_chars_per_chunk:
                current_chunk += page_text + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = page_text + "\n\n"

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks
