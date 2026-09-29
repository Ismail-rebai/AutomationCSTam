"""
Tokenizer for BM25 and text processing.

Handles: lowercase, Unicode accent folding, punctuation stripping,
French+English stopwords, and preservation of tech tokens
like C#, .NET, Node.js, CI/CD.
"""

import re
import unicodedata
from typing import List


# --- Tech tokens that should be preserved as-is (lowered) ---
# Order matters: longer patterns first to avoid partial matches.
TECH_TOKENS_RAW = [
    "ASP.NET Core", "ASP.NET", ".NET Core", ".NET",
    "Node.js", "Vue.js", "Next.js", "Express.js", "Nuxt.js", "Three.js",
    "CI/CD", "C#", "C++", "F#",
    "S/4HANA", "FI/CO",
    "Power BI", "HL7 FHIR",
    "ISO 27001", "ISO 27005",
    "React Native",
    "Spring Boot", "Spring Cloud",
    "Entity Framework",
    "Lightning Web Components",
]

# Build a regex pattern that matches tech tokens (case-insensitive).
# Escape dots and special chars, sort by length descending.
_tech_sorted = sorted(TECH_TOKENS_RAW, key=len, reverse=True)
_tech_pattern = re.compile(
    "|".join(re.escape(t) for t in _tech_sorted),
    re.IGNORECASE,
)

# --- Stopwords ---
FRENCH_STOPWORDS = frozenset(
    "le la les un une des de du d l au aux en et est sont "
    "a à ce ces cet cette il ils elle elles on nous vous je tu "
    "qui que qu quoi dont où ou mais pour par sur dans avec sans "
    "ne pas plus moins très tout tous toute toutes "
    "son sa ses mon ma mes notre nos votre vos leur leurs "
    "être avoir fait faire peut peuvent aussi bien entre autre autres "
    "si se ni même comme ça car donc "
    "y c s n j m t".split()
)

ENGLISH_STOPWORDS = frozenset(
    "the a an and or but in on at to for of is are was were "
    "be been being have has had do does did will would shall should "
    "can could may might must not no nor so if then than that "
    "this these those it its he she they we you i me him her "
    "them my your his our their what which who whom how when where "
    "why all each every both few more most other some such only "
    "with from by as into through during before after above below "
    "between out about up over down again further once here there".split()
)

ALL_STOPWORDS = FRENCH_STOPWORDS | ENGLISH_STOPWORDS


def _fold_accents(text: str) -> str:
    """Remove diacritics / accents via Unicode NFD decomposition."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if unicodedata.category(c) != "Mn")


def tokenize(text: str) -> List[str]:
    """
    Tokenize text for BM25 indexing / querying.

    Steps:
    1. Extract and protect tech tokens (multi-word compounds).
    2. Fold accents (système -> systeme).
    3. Lowercase.
    4. Strip punctuation (except inside protected tokens).
    5. Remove stopwords.
    6. Remove single-character tokens (except protected ones like 'c#').
    """
    if not text:
        return []

    # Step 1: extract tech tokens and replace them with placeholders
    protected: list[str] = []
    placeholder_map: dict[str, str] = {}

    def _replace_tech(match: re.Match) -> str:
        token = match.group(0).lower()
        # Normalize the token: replace spaces with underscore for compound tokens
        normalized = token.replace(" ", "_")
        ph = f"__TECH{len(protected)}__"
        protected.append(normalized)
        placeholder_map[ph] = normalized
        return f" {ph} "

    text_with_ph = _tech_pattern.sub(_replace_tech, text)

    # Step 2: fold accents
    text_folded = _fold_accents(text_with_ph)

    # Step 3: lowercase
    text_lower = text_folded.lower()

    # Step 4: strip punctuation but keep placeholders and alphanumeric
    # Replace punctuation with space (except underscores in placeholders)
    cleaned = re.sub(r"[^\w\s]", " ", text_lower)

    # Step 5: split and process
    raw_tokens = cleaned.split()

    result: list[str] = []
    for tok in raw_tokens:
        # Check if it's a placeholder
        ph_key = tok.upper()
        if ph_key.startswith("__TECH") and ph_key.endswith("__"):
            # Map back to the real tech token
            if ph_key in placeholder_map:
                result.append(placeholder_map[ph_key])
            else:
                result.append(tok)
            continue

        # Skip stopwords
        if tok in ALL_STOPWORDS:
            continue

        # Skip single-char tokens and pure numbers
        if len(tok) <= 1 or tok.isdigit():
            continue

        result.append(tok)

    return result
