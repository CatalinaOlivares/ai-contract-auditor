"""
Dataset loader for CUAD (Contract Understanding Atticus Dataset).

Source: https://huggingface.co/datasets/theatticusproject/cuad

The CUAD dataset contains:
- 510 commercial legal contracts as PDFs
- Each PDF is a real legal contract
"""

from datasets import load_dataset
from typing import List, Optional, Dict, Any
import random
import io


class CUADDatasetLoader:
    """Loader for the CUAD dataset from HuggingFace."""

    DATASET_NAME = "theatticusproject/cuad"

    def __init__(self):
        self._dataset = None

    def load(self) -> None:
        """Load the CUAD dataset from HuggingFace."""
        if self._dataset is None:
            print("Loading CUAD dataset from HuggingFace...")
            self._dataset = load_dataset(
                self.DATASET_NAME,
                verification_mode="no_checks"
            )
            print(f"Dataset loaded. Contracts: {len(self._dataset['train'])}")

    @property
    def dataset(self):
        """Get the loaded dataset, loading it if necessary."""
        if self._dataset is None:
            self.load()
        return self._dataset

    def _extract_text_from_pdf(self, pdf_obj) -> str:
        """Extract text from a pdfplumber PDF object."""
        text_parts = []
        try:
            for page in pdf_obj.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        except Exception as e:
            print(f"Error extracting PDF text: {e}")
        return "\n\n".join(text_parts)

    def _get_pdf_bytes(self, pdf_obj) -> Optional[bytes]:
        """Extract PDF bytes from a pdfplumber PDF object."""
        try:
            # pdfplumber PDF object has a stream attribute with the file path
            if hasattr(pdf_obj, 'stream') and pdf_obj.stream:
                pdf_obj.stream.seek(0)
                return pdf_obj.stream.read()
        except Exception as e:
            print(f"Error extracting PDF bytes: {e}")
        return None

    def get_sample_contracts(self, n: int = 5, seed: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get n sample contracts from the dataset.

        Args:
            n: Number of contracts to retrieve
            seed: Random seed for reproducibility

        Returns:
            List of contract dictionaries with text content
        """
        if seed is not None:
            random.seed(seed)

        train_data = self.dataset['train']
        total = len(train_data)

        # Select random indices
        indices = random.sample(range(total), min(n, total))

        contracts = []
        for idx in indices:
            try:
                entry = train_data[idx]
                pdf_obj = entry['pdf']

                # Extract text from PDF
                text = self._extract_text_from_pdf(pdf_obj)

                # Extract PDF bytes
                pdf_bytes = self._get_pdf_bytes(pdf_obj)

                if text.strip():
                    contracts.append({
                        'title': f"CUAD_Contract_{idx}",
                        'text': text,
                        'pdf_bytes': pdf_bytes,
                        'index': idx,
                    })
            except Exception as e:
                print(f"Error processing contract {idx}: {e}")
                continue

        return contracts

    def get_contract_by_index(self, index: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific contract by its index.

        Args:
            index: The contract index in the dataset

        Returns:
            Contract dictionary or None if not found
        """
        train_data = self.dataset['train']

        if index < 0 or index >= len(train_data):
            return None

        try:
            entry = train_data[index]
            pdf_obj = entry['pdf']
            text = self._extract_text_from_pdf(pdf_obj)

            return {
                'title': f"CUAD_Contract_{index}",
                'text': text,
                'index': index,
            }
        except Exception as e:
            print(f"Error getting contract {index}: {e}")
            return None

    def get_statistics(self) -> Dict[str, Any]:
        """Get dataset statistics."""
        train_data = self.dataset['train']

        return {
            'total_contracts': len(train_data),
            'source': 'https://huggingface.co/datasets/theatticusproject/cuad',
            'description': 'Contract Understanding Atticus Dataset - 510 commercial legal contracts',
        }


# Singleton instance for reuse
_loader_instance = None


def get_dataset_loader() -> CUADDatasetLoader:
    """Get the singleton dataset loader instance."""
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = CUADDatasetLoader()
    return _loader_instance
