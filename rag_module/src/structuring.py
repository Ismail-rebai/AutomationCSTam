"""
Tender structuring: convert raw tender descriptions (French) into
the target tender schema using Groq's OpenAI-compatible API.

Features:
- Pydantic v2 strict validation.
- One retry with validation error fed back to LLM.
- Deterministic fallback (single-requirement stub).
- Never crashes on malformed model output.
- Never invents facts: absent fields stay null/empty.
"""

import json
import logging
import os
from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)


# --- Target Tender Schema (Pydantic v2) ---


class Buyer(BaseModel):
    name: Optional[str] = None
    sector: Optional[str] = None  # public | private


class Lot(BaseModel):
    lot_id: int
    description: str


class Requirement(BaseModel):
    req_id: str
    text: str
    category: Optional[str] = None  # technical | compliance | administrative | financial
    tech_keywords: List[str] = Field(default_factory=list)


class EvaluationCriterion(BaseModel):
    criterion: str
    weight: Optional[float] = None


class StructuredTender(BaseModel):
    """The target structured tender schema."""

    tender_id: str
    source: Optional[str] = None
    source_url: Optional[str] = None
    language: str = "fr"
    buyer: Optional[Buyer] = None
    title: Optional[str] = None
    publication_date: Optional[str] = None  # YYYY-MM-DD
    submission_deadline: Optional[str] = None  # YYYY-MM-DD
    estimated_budget: Optional[str] = None
    lots: List[Lot] = Field(default_factory=list)
    eligibility: List[str] = Field(default_factory=list)
    requirements: List[Requirement] = Field(default_factory=list)
    evaluation_criteria: List[EvaluationCriterion] = Field(default_factory=list)
    raw_text_ref: Optional[str] = None
    structuring_status: str = "success"  # success | fallback | error


# --- LLM Extraction Prompt ---

STRUCTURING_PROMPT = """You are an expert at extracting structured information from French tender descriptions (appels d'offres).

Given the raw tender data below, extract the information into the specified JSON schema.

RULES:
1. Extract ONLY what is explicitly stated. Do NOT invent or assume information.
2. If a field is not mentioned, set it to null or empty array.
3. Requirements should be atomic: break down compound requirements into separate items.
4. For each requirement, assign a category: "technical", "compliance", "administrative", or "financial".
5. Extract tech_keywords from each requirement (programming languages, frameworks, tools, standards).
6. If lots are mentioned, list them. Otherwise leave lots empty.
7. Dates should be in YYYY-MM-DD format. Convert from French date formats.
8. The tender_id must match the provided tender_id.
9. Output ONLY valid JSON matching the schema. No markdown, no explanation.

RAW TENDER DATA:
{raw_data}

JSON SCHEMA (your output must match this exactly):
{{
  "tender_id": "string",
  "source": "string or null",
  "source_url": "string or null",
  "language": "fr",
  "buyer": {{"name": "string or null", "sector": "public or private or null"}},
  "title": "string or null",
  "publication_date": "YYYY-MM-DD or null",
  "submission_deadline": "YYYY-MM-DD or null",
  "estimated_budget": "string or null",
  "lots": [{{"lot_id": 1, "description": "string"}}],
  "eligibility": ["string"],
  "requirements": [{{"req_id": "R1", "text": "string", "category": "technical|compliance|administrative|financial", "tech_keywords": ["string"]}}],
  "evaluation_criteria": [{{"criterion": "string", "weight": number_or_null}}],
  "raw_text_ref": null,
  "structuring_status": "success"
}}"""

RETRY_PROMPT = """The previous output failed validation with this error:
{error}

Please fix the output to match the schema. Output ONLY valid JSON."""


def _create_fallback(raw_tender: dict) -> StructuredTender:
    """
    Deterministic fallback: wrap the whole description as a single requirement.
    Used when LLM is unavailable or fails.
    """
    tender_id = raw_tender.get("tender_id") or raw_tender.get("id", "UNKNOWN")
    desc = raw_tender.get("description", "")
    title = raw_tender.get("title", desc[:100])

    return StructuredTender(
        tender_id=tender_id,
        source=raw_tender.get("source"),
        source_url=raw_tender.get("url") or raw_tender.get("source_url"),
        language=raw_tender.get("language", "fr"),
        buyer=Buyer(
            name=raw_tender.get("buyer"),
            sector=None,
        ) if raw_tender.get("buyer") else None,
        title=title,
        publication_date=raw_tender.get("publication_date") or raw_tender.get("published_date"),
        submission_deadline=raw_tender.get("submission_deadline") or raw_tender.get("deadline"),
        requirements=[
            Requirement(
                req_id="R1",
                text=desc,
                category="technical",
                tech_keywords=[],
            )
        ] if desc else [],
        structuring_status="fallback",
    )


def _parse_llm_output(raw_json: str, tender_id: str) -> StructuredTender:
    """
    Parse and validate LLM output.

    Handles common LLM quirks: markdown code fences, leading text, etc.
    """
    # Strip markdown code fences
    text = raw_json.strip()
    if text.startswith("```"):
        # Remove opening fence (possibly with language tag)
        first_newline = text.index("\n") if "\n" in text else 3
        text = text[first_newline + 1:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    # Try to find JSON object
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        text = text[start:end]

    parsed = json.loads(text)

    # Ensure tender_id matches
    parsed["tender_id"] = tender_id

    return StructuredTender(**parsed)


async def structure_tender(
    raw_tender: dict,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    base_url: str = "https://api.groq.com/openai/v1",
) -> StructuredTender:
    """
    Structure a raw tender using LLM (Groq).

    Falls back to deterministic structuring if LLM is unavailable.

    Args:
        raw_tender: dict with at least 'description' and 'tender_id'/'id'.
        api_key: Groq API key (or from GROQ_API_KEY env var).
        model: Groq model name (or from GROQ_MODEL env var).
        base_url: API base URL.

    Returns:
        StructuredTender with structuring_status indicating method used.
    """
    key = api_key or os.getenv("GROQ_API_KEY", "")
    mdl = model or os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
    tender_id = raw_tender.get("tender_id") or raw_tender.get("id", "UNKNOWN")

    if not key:
        logger.warning("No GROQ_API_KEY set; using fallback structuring")
        return _create_fallback(raw_tender)

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=key, base_url=base_url)

        raw_data_str = json.dumps(raw_tender, ensure_ascii=False, indent=2)
        prompt = STRUCTURING_PROMPT.format(raw_data=raw_data_str)

        # First attempt
        response = await client.chat.completions.create(
            model=mdl,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"},
            max_tokens=4096,
        )

        llm_output = response.choices[0].message.content or ""

        try:
            result = _parse_llm_output(llm_output, tender_id)
            return result
        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning("First LLM attempt failed validation: %s", e)

            # Retry with error feedback
            retry_msg = RETRY_PROMPT.format(error=str(e))
            retry_response = await client.chat.completions.create(
                model=mdl,
                messages=[
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": llm_output},
                    {"role": "user", "content": retry_msg},
                ],
                temperature=0,
                response_format={"type": "json_object"},
                max_tokens=4096,
            )

            retry_output = retry_response.choices[0].message.content or ""

            try:
                result = _parse_llm_output(retry_output, tender_id)
                return result
            except Exception as e2:
                logger.error("Retry also failed: %s. Using fallback.", e2)
                return _create_fallback(raw_tender)

    except ImportError:
        logger.warning("openai package not installed; using fallback structuring")
        return _create_fallback(raw_tender)
    except Exception as e:
        logger.error("LLM structuring failed: %s. Using fallback.", e)
        return _create_fallback(raw_tender)


def structure_tender_sync(raw_tender: dict, **kwargs) -> StructuredTender:
    """Synchronous wrapper for structure_tender."""
    import asyncio

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # We're inside an async context; create a new task
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            result = pool.submit(
                asyncio.run, structure_tender(raw_tender, **kwargs)
            ).result()
        return result
    else:
        return asyncio.run(structure_tender(raw_tender, **kwargs))
