from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Optional
import json

from core.config import settings
from api.schemas.contract import ExtractedDataSchema, PartySchema


class LLMExtractionResult(BaseModel):
    """Internal schema for LLM extraction output."""

    parties: List[dict] = Field(default_factory=list, description="List of parties with name and role")
    effective_date: Optional[str] = Field(None, description="Contract start date in ISO format (YYYY-MM-DD)")
    contract_duration_months: Optional[int] = Field(None, description="Duration in months as integer")
    contract_duration_raw: Optional[str] = Field(None, description="Original duration text from contract")
    jurisdiction: Optional[str] = Field(None, description="Governing law jurisdiction")
    risk_score: int = Field(50, ge=1, le=100, description="Risk score 1-100")
    confidence: float = Field(0.8, ge=0, le=1, description="Extraction confidence")


class ExtractionChain:
    """LangChain-based extraction service using Gemini."""

    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0,  # Deterministic for extraction
        )
        self.parser = PydanticOutputParser(pydantic_object=LLMExtractionResult)

    def _build_prompt(self) -> ChatPromptTemplate:
        """Build the extraction prompt template."""
        return ChatPromptTemplate.from_messages([
            ("system", """You are an expert legal analyst specializing in contract information extraction.
Your task is to extract structured data from the provided contract text.

IMPORTANT INSTRUCTIONS:

1. Extract ONLY information that explicitly appears in the text

2. For effective_date: Convert to ISO format (YYYY-MM-DD)
   IMPORTANT: Dates may be in DAY-MONTH-YEAR format (common in Latin America and Europe)
   - Support Spanish months: Enero, Febrero, Marzo, Abril, Mayo, Junio, Julio, Agosto, Septiembre, Octubre, Noviembre, Diciembre
   - Support English months: January, February, March, April, May, June, July, August, September, October, November, December
   - Examples:
     * "15 de Enero de 2024" -> "2024-01-15"
     * "15, Enero, 2024" -> "2024-01-15"
     * "January 15, 2024" -> "2024-01-15"
     * "15/01/2024" -> "2024-01-15" (DD/MM/YYYY format)
     * "15-01-2024" -> "2024-01-15" (DD-MM-YYYY format)
     * "2024-01-15" -> "2024-01-15" (already ISO format)
   - ASSUME DD/MM/YYYY format for numeric dates (day first, then month)

3. For duration: convert to integer months (DO NOT round up partial periods)
   - "one year" = 12 months
   - "two years" = 24 months
   - "two years and one day" = 24 months (store the extra days in contract_duration_raw)
   - "18 months" = 18 months
   - "one and a half years" = 18 months
   - "un año" = 12 months
   - "dos años" = 24 months
   - "indefinite" / "indefinido" or not found = null
   IMPORTANT: Always store the EXACT original text in contract_duration_raw field

4. For risk_score: analyze the contract language
   - Unilateral clauses, excessive penalties = high score (70-100)
   - Balanced language, mutual protections = low score (1-30)
   - Standard terms = medium score (30-70)

5. If you cannot find a field, use null

6. For parties: extract name and role (Seller/Vendedor, Buyer/Comprador, Licensor, Licensee, etc.)

7. For jurisdiction: extract the governing law location (city/state/country)

{format_instructions}

RESPOND ONLY WITH THE JSON. NO ADDITIONAL TEXT."""),
            ("human", """Extract structured information from this contract:

--- CONTRACT START ---
{contract_text}
--- CONTRACT END ---

Return the JSON with extracted data:""")
        ])

    async def extract(self, contract_text: str) -> tuple[ExtractedDataSchema, float]:
        """
        Extract structured data from contract text.

        Args:
            contract_text: The raw text of the contract

        Returns:
            Tuple of (ExtractedDataSchema, confidence_score)
        """
        prompt = self._build_prompt()
        format_instructions = self.parser.get_format_instructions()

        # Truncate if too long (Gemini has token limits)
        max_chars = 30000  # Safe limit for context
        if len(contract_text) > max_chars:
            contract_text = contract_text[:max_chars] + "\n\n[... TRUNCATED ...]"

        try:
            # Create and invoke the chain
            chain = prompt | self.llm

            result = await chain.ainvoke({
                "contract_text": contract_text,
                "format_instructions": format_instructions
            })

            # Parse the response
            response_text = result.content

            # Try to extract JSON from the response
            parsed = self._parse_response(response_text)

            # Convert to our schema
            extracted_data = ExtractedDataSchema(
                parties=[
                    PartySchema(name=p.get("name", "Unknown"), role=p.get("role"))
                    for p in parsed.parties
                ],
                effective_date=parsed.effective_date,
                contract_duration_months=parsed.contract_duration_months,
                contract_duration_raw=parsed.contract_duration_raw,
                jurisdiction=parsed.jurisdiction,
                risk_score=parsed.risk_score
            )

            return extracted_data, parsed.confidence

        except Exception as e:
            # Log the error for debugging
            import logging
            logging.error(f"LLM Extraction failed: {type(e).__name__}: {e}")
            # Return default with low confidence on error
            return ExtractedDataSchema(risk_score=50), 0.0

    def _parse_response(self, response_text: str) -> LLMExtractionResult:
        """Parse the LLM response into structured data."""
        try:
            # Try to find JSON in the response
            text = response_text.strip()

            # Handle markdown code blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            # Parse JSON
            data = json.loads(text)
            return LLMExtractionResult(**data)
        except json.JSONDecodeError:
            # Try to parse with the Pydantic parser
            try:
                return self.parser.parse(response_text)
            except Exception:
                return LLMExtractionResult()

    def extract_sync(self, contract_text: str) -> tuple[ExtractedDataSchema, float]:
        """Synchronous version of extract for non-async contexts."""
        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.extract(contract_text))
