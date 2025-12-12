from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from typing import List, Optional
from pydantic import BaseModel
import json
import re

from core.config import settings
from api.schemas.contract import ExtractedDataSchema, ValidationIssue


class DurationParseResult(BaseModel):
    """Result of parsing a duration text."""
    months: Optional[int]
    has_extra_days: bool = False  # True if there are days beyond complete months
    reasoning: str


class ValidationResult(BaseModel):
    """Complete validation result."""
    issues: List[ValidationIssue]
    requires_review: bool
    review_reasons: List[str]


class ValidationAgent:
    """
    Agent for validating extracted contract data against business rules.

    This agent can:
    1. Validate durations (e.g., "two years and one day" exceeds 24 months)
    2. Apply business rules
    3. Reason about edge cases

    IMPORTANT: Duration validation checks if the contract exceeds 24 months,
    including partial periods (days/weeks). "24 months and 1 day" exceeds the limit.
    """

    BUSINESS_RULES = [
        {
            "id": "duration_24_months",
            "description": "Duration exceeds 24 months",
            "field": "contract_duration_months",
        },
        {
            "id": "jurisdiction_not_chile",
            "description": "Jurisdiction is not Chile",
            "field": "jurisdiction",
        },
        {
            "id": "high_risk_score",
            "description": "High risk score (>70)",
            "field": "risk_score",
        },
    ]

    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0,
        )

    async def parse_duration_text(self, duration_text: str) -> DurationParseResult:
        """
        Analyze duration text to determine if it exceeds 24 months.

        Examples:
        - "two years" -> 24 months, does NOT exceed
        - "two years and one day" -> 24 months + extra days, EXCEEDS 24 months
        - "twenty-five months" -> 25 months, EXCEEDS
        - "eighteen months" -> 18 months, does NOT exceed
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at interpreting contract duration terms.
Analyze the duration and determine the number of COMPLETE months.

RULES:
- 1 year = 12 months
- DO NOT round up partial periods to the next month
- "two years" = 24 months
- "two years and one day" = 24 months (but note there are extra days)
- "one and a half years" = 18 months
- Report if there are extra days/weeks beyond complete months

Respond with JSON only:
{{
  "months": <integer number of complete months, or null if indefinite>,
  "has_extra_days": <true if there are additional days beyond complete months>,
  "reasoning": "<explanation>"
}}"""),
            ("human", "Analyze this duration: \"{duration_text}\"")
        ])

        try:
            chain = prompt | self.llm
            result = await chain.ainvoke({"duration_text": duration_text})

            # Parse response
            text = result.content.strip()
            if "```" in text:
                text = text.split("```")[1].split("```")[0]
                if text.startswith("json"):
                    text = text[4:]

            data = json.loads(text)
            return DurationParseResult(
                months=data.get("months"),
                has_extra_days=data.get("has_extra_days", False),
                reasoning=data.get("reasoning", "")
            )
        except Exception as e:
            # Fallback: try simple pattern matching
            return self._parse_duration_fallback(duration_text)

    def _parse_duration_fallback(self, text: str) -> DurationParseResult:
        """Fallback duration parsing with regex patterns."""
        text = text.lower().strip()

        # Patterns for common formats
        patterns = [
            # "X years" or "X year"
            (r"(\d+)\s*years?", lambda m: int(m.group(1)) * 12),
            # "X months" or "X month"
            (r"(\d+)\s*months?", lambda m: int(m.group(1))),
            # "X years and Y months"
            (r"(\d+)\s*years?\s*(?:and\s*)?(\d+)\s*months?",
             lambda m: int(m.group(1)) * 12 + int(m.group(2))),
        ]

        # Word to number mapping
        word_nums = {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
            "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
            "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
            "nineteen": 19, "twenty": 20, "twenty-one": 21, "twenty-two": 22,
            "twenty-three": 23, "twenty-four": 24, "twenty-five": 25,
            "thirty": 30, "thirty-six": 36
        }

        # Try numeric patterns first
        for pattern, converter in patterns:
            match = re.search(pattern, text)
            if match:
                months = converter(match)
                # Check for "and one day" or similar -> mark as has_extra_days (DON'T add months)
                has_extra = bool(re.search(r"and\s*(one|a|\d+)\s*days?", text))
                return DurationParseResult(
                    months=months,
                    has_extra_days=has_extra,
                    reasoning=f"Pattern match: {pattern}" + (" (with extra days)" if has_extra else "")
                )

        # Try word-based patterns with regex to match word directly before year/month
        # Sort by length descending to match "twenty-four" before "four"
        sorted_words = sorted(word_nums.keys(), key=len, reverse=True)

        for word in sorted_words:
            num = word_nums[word]
            # Match word directly followed by year(s)
            year_match = re.search(rf"\b{re.escape(word)}\s+years?\b", text)
            if year_match:
                months = num * 12
                has_extra = bool(re.search(r"\band\s+(one|a|\d+)\s+days?\b", text))
                return DurationParseResult(
                    months=months,
                    has_extra_days=has_extra,
                    reasoning=f"Word match: {word} years" + (" (with extra days)" if has_extra else "")
                )

            # Match word directly followed by month(s)
            month_match = re.search(rf"\b{re.escape(word)}\s+months?\b", text)
            if month_match:
                has_extra = bool(re.search(r"\band\s+(one|a|\d+)\s+days?\b", text))
                return DurationParseResult(
                    months=num,
                    has_extra_days=has_extra,
                    reasoning=f"Word match: {word} months" + (" (with extra days)" if has_extra else "")
                )

        return DurationParseResult(months=None, reasoning="Could not parse duration")

    async def validate(self, extracted_data: ExtractedDataSchema) -> ValidationResult:
        """
        Validate extracted data against business rules.

        Rules:
        1. Duration > 24 months -> REQUIRES_HUMAN_REVIEW
        2. Jurisdiction != Chile -> REQUIRES_HUMAN_REVIEW
        3. Risk score > 70 -> REQUIRES_HUMAN_REVIEW
        """
        issues = []
        review_reasons = []
        requires_review = False

        # Rule 1: Check duration
        duration_issue = await self._check_duration_rule(extracted_data)
        if duration_issue:
            issues.append(duration_issue)
            requires_review = True
            review_reasons.append(
                f"Duration exceeds 24 months: {extracted_data.contract_duration_months or 'unknown'} months"
            )

        # Rule 2: Check jurisdiction
        jurisdiction_issue = self._check_jurisdiction_rule(extracted_data)
        if jurisdiction_issue:
            issues.append(jurisdiction_issue)
            requires_review = True
            review_reasons.append(
                f"Jurisdiction is not Chile: {extracted_data.jurisdiction}"
            )

        # Rule 3: Check risk score
        risk_issue = self._check_risk_rule(extracted_data)
        if risk_issue:
            issues.append(risk_issue)
            requires_review = True
            review_reasons.append(
                f"High risk score: {extracted_data.risk_score}/100"
            )

        return ValidationResult(
            issues=issues,
            requires_review=requires_review,
            review_reasons=review_reasons
        )

    async def _check_duration_rule(
        self,
        data: ExtractedDataSchema
    ) -> Optional[ValidationIssue]:
        """Check if duration exceeds 24 months.

        IMPORTANT: Duration EXCEEDS 24 months if:
        - months > 24, OR
        - months == 24 AND there are extra days (e.g., "two years and one day")
        """
        duration_months = data.contract_duration_months
        has_extra_days = False

        # If we have raw text but no parsed months, try to parse
        if data.contract_duration_raw:
            parse_result = await self.parse_duration_text(data.contract_duration_raw)
            if duration_months is None:
                duration_months = parse_result.months
            has_extra_days = parse_result.has_extra_days

        # Check if exceeds 24 months:
        # - More than 24 months, OR
        # - Exactly 24 months with extra days
        exceeds_limit = False
        if duration_months is not None:
            if duration_months > 24:
                exceeds_limit = True
            elif duration_months == 24 and has_extra_days:
                exceeds_limit = True

        if exceeds_limit:
            extra_info = " (plus extra days)" if has_extra_days else ""
            return ValidationIssue(
                field="contract_duration_months",
                rule="duration_24_months",
                message=f"Contract duration of {duration_months} months{extra_info} exceeds the 24-month limit",
                severity="warning",
                reasoning=f"Original text: '{data.contract_duration_raw}' -> {duration_months} months{extra_info}"
            )

        return None

    def _check_jurisdiction_rule(
        self,
        data: ExtractedDataSchema
    ) -> Optional[ValidationIssue]:
        """Check if jurisdiction is not Chile."""
        if not data.jurisdiction:
            return None

        jurisdiction_lower = data.jurisdiction.lower()
        chile_indicators = ["chile", "santiago", "valparaiso", "concepcion", "chilean"]

        is_chile = any(ind in jurisdiction_lower for ind in chile_indicators)

        if not is_chile:
            return ValidationIssue(
                field="jurisdiction",
                rule="jurisdiction_not_chile",
                message=f"Jurisdiction '{data.jurisdiction}' is not Chile",
                severity="warning",
                reasoning="Contracts with foreign jurisdiction require special legal review"
            )

        return None

    def _check_risk_rule(
        self,
        data: ExtractedDataSchema
    ) -> Optional[ValidationIssue]:
        """Check if risk score is high."""
        if data.risk_score > 70:
            return ValidationIssue(
                field="risk_score",
                rule="high_risk_score",
                message=f"High risk score: {data.risk_score}/100",
                severity="error",
                reasoning="Aggressive language detected that requires legal review"
            )

        return None
