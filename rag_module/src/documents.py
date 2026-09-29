"""
Document loading and KB record flattening.

Loads CVs, projects, clients, and tech_stack from JSON files,
flattens each record into a retrievable text string with metadata.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DATA_DIR = Path(os.getenv("DATA_DIR", Path(__file__).parent.parent / "data"))


@dataclass
class KBRecord:
    """A single retrievable knowledge-base record."""

    record_id: str
    record_type: str  # cv | past_project | client | tech_stack
    text: str  # flattened text for embedding / BM25
    metadata: Dict[str, Any] = field(default_factory=dict)


def _load_json(filename: str) -> list:
    """Load a JSON array file from DATA_DIR."""
    path = DATA_DIR / filename
    if not path.exists():
        logger.warning("Data file not found: %s", path)
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def flatten_cv(cv: dict) -> KBRecord:
    """Flatten a CV record into searchable text."""
    skills = ", ".join(cv.get("skills", []))
    certs = ", ".join(cv.get("certifications", [])) if cv.get("certifications") else "None"
    langs = ", ".join(cv.get("languages", []))
    projects = ", ".join(cv.get("projects", []))

    text = (
        f"{cv['name']} - {cv['title']}. "
        f"{cv.get('years_experience', 0)} years of experience. "
        f"Skills: {skills}. "
        f"Certifications: {certs}. "
        f"Languages: {langs}. "
        f"Education: {cv.get('education', 'N/A')}. "
        f"Projects: {projects}. "
        f"{cv.get('summary', '')}"
    )
    return KBRecord(
        record_id=cv["cv_id"],
        record_type="cv",
        text=text,
        metadata={
            "name": cv["name"],
            "title": cv["title"],
            "skills": cv.get("skills", []),
            "years_experience": cv.get("years_experience", 0),
            "projects": cv.get("projects", []),
            "certifications": cv.get("certifications", []),
        },
    )


def flatten_project(proj: dict) -> KBRecord:
    """Flatten a project record into searchable text."""
    techs = ", ".join(proj.get("technologies", []))
    team = ", ".join(proj.get("team_cvs", []))
    deliverables = ", ".join(proj.get("deliverables", []))

    text = (
        f"Project: {proj['name']}. "
        f"Client: {proj.get('client_id', 'N/A')}. "
        f"Domain: {proj.get('domain', 'N/A')}. "
        f"Year: {proj.get('year', 'N/A')}. "
        f"Duration: {proj.get('duration_months', 'N/A')} months. "
        f"Status: {proj.get('status', 'N/A')}. "
        f"Technologies: {techs}. "
        f"Team: {team}. "
        f"Deliverables: {deliverables}. "
        f"{proj.get('description', '')} "
        f"Outcomes: {proj.get('outcomes', '')}"
    )
    return KBRecord(
        record_id=proj["project_id"],
        record_type="past_project",
        text=text,
        metadata={
            "name": proj["name"],
            "client_id": proj.get("client_id"),
            "domain": proj.get("domain"),
            "technologies": proj.get("technologies", []),
            "team_cvs": proj.get("team_cvs", []),
            "year": proj.get("year"),
        },
    )


def flatten_client(client: dict) -> KBRecord:
    """Flatten a client portfolio record into searchable text."""
    engagements_text = []
    for eng in client.get("engagements", []):
        engagements_text.append(
            f"{eng.get('project_id', 'N/A')} ({eng.get('year', 'N/A')}): "
            f"{eng.get('scope', 'N/A')} [satisfaction: {eng.get('satisfaction', 'N/A')}]"
        )
    eng_str = "; ".join(engagements_text)
    techs = ", ".join(client.get("technologies_deployed", []))

    text = (
        f"Client: {client['name']}. "
        f"Sector: {client.get('sector', 'N/A')}. "
        f"Type: {client.get('type', 'N/A')}. "
        f"Country: {client.get('country', 'N/A')}. "
        f"{client.get('description', '')} "
        f"Engagements: {eng_str}. "
        f"Technologies deployed: {techs}. "
        f"Relationship since: {client.get('relationship_since', 'N/A')}. "
        f"{client.get('outcomes_summary', '')}"
    )
    return KBRecord(
        record_id=client["client_id"],
        record_type="client",
        text=text,
        metadata={
            "name": client["name"],
            "sector": client.get("sector"),
            "type": client.get("type"),
            "engagements": client.get("engagements", []),
            "technologies_deployed": client.get("technologies_deployed", []),
        },
    )


def flatten_tech(tech: dict) -> KBRecord:
    """Flatten a tech stack record into searchable text."""
    projects = ", ".join(tech.get("projects", []))
    cvs = ", ".join(tech.get("cvs", []))
    related = ", ".join(tech.get("related_technologies", []))
    versions = ", ".join(tech.get("versions_used", []))

    text = (
        f"Technology: {tech['name']}. "
        f"Category: {tech.get('category', 'N/A')}. "
        f"Maturity: {tech.get('maturity', 'N/A')}. "
        f"Versions: {versions}. "
        f"{tech.get('description', '')} "
        f"Used in projects: {projects}. "
        f"Team members: {cvs}. "
        f"Related technologies: {related}."
    )
    return KBRecord(
        record_id=tech["tech_id"],
        record_type="tech_stack",
        text=text,
        metadata={
            "name": tech["name"],
            "category": tech.get("category"),
            "maturity": tech.get("maturity"),
            "projects": tech.get("projects", []),
            "cvs": tech.get("cvs", []),
        },
    )


def load_all_records(data_dir: Optional[str] = None) -> List[KBRecord]:
    """
    Load all KB records from data files.

    Returns a list of KBRecord with record_type in
    {cv, past_project, client, tech_stack}.
    """
    global DATA_DIR
    if data_dir:
        DATA_DIR = Path(data_dir)

    records: List[KBRecord] = []

    # CVs
    cvs = _load_json("cvs.json")
    for cv in cvs:
        records.append(flatten_cv(cv))
    logger.info("Loaded %d CVs", len(cvs))

    # Projects
    projects = _load_json("projects.json")
    for proj in projects:
        records.append(flatten_project(proj))
    logger.info("Loaded %d projects", len(projects))

    # Clients
    clients = _load_json("clients.json")
    for client in clients:
        records.append(flatten_client(client))
    logger.info("Loaded %d clients", len(clients))

    # Tech stack
    techs = _load_json("tech_stack.json")
    for tech in techs:
        records.append(flatten_tech(tech))
    logger.info("Loaded %d tech stack entries", len(techs))

    logger.info("Total KB records: %d", len(records))
    return records


def load_gold_set(data_dir: Optional[str] = None) -> list:
    """Load the gold evaluation set."""
    global DATA_DIR
    if data_dir:
        DATA_DIR = Path(data_dir)
    return _load_json("gold_matches.json")


def load_stub_tenders(data_dir: Optional[str] = None) -> list:
    """Load stub tenders for testing."""
    global DATA_DIR
    if data_dir:
        DATA_DIR = Path(data_dir)
    return _load_json("tenders_stub.json")
