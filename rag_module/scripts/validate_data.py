"""
Validate data consistency across KB files.

Checks:
1. All project IDs referenced in CVs exist in projects.json
2. All CV IDs referenced in projects exist in cvs.json
3. All client IDs referenced in projects exist in clients.json
4. All project/CV IDs referenced in tech_stack exist
5. No duplicate IDs within any file
6. Required fields are present
"""

import json
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


def load(filename):
    with open(DATA_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


def validate():
    errors = []
    warnings = []

    # Load all data
    cvs = load("cvs.json")
    projects = load("projects.json")
    clients = load("clients.json")
    tech_stack = load("tech_stack.json")

    # Build ID sets
    cv_ids = set()
    for cv in cvs:
        if cv["cv_id"] in cv_ids:
            errors.append(f"Duplicate CV ID: {cv['cv_id']}")
        cv_ids.add(cv["cv_id"])

    proj_ids = set()
    for proj in projects:
        if proj["project_id"] in proj_ids:
            errors.append(f"Duplicate project ID: {proj['project_id']}")
        proj_ids.add(proj["project_id"])

    client_ids = set()
    for client in clients:
        if client["client_id"] in client_ids:
            errors.append(f"Duplicate client ID: {client['client_id']}")
        client_ids.add(client["client_id"])

    tech_ids = set()
    for tech in tech_stack:
        if tech["tech_id"] in tech_ids:
            errors.append(f"Duplicate tech ID: {tech['tech_id']}")
        tech_ids.add(tech["tech_id"])

    # Cross-reference checks

    # CVs -> Projects
    for cv in cvs:
        for pid in cv.get("projects", []):
            if pid not in proj_ids:
                errors.append(f"CV {cv['cv_id']} references non-existent project {pid}")

    # Projects -> CVs
    for proj in projects:
        for cid in proj.get("team_cvs", []):
            if cid not in cv_ids:
                errors.append(f"Project {proj['project_id']} references non-existent CV {cid}")

    # Projects -> Clients
    for proj in projects:
        cid = proj.get("client_id")
        if cid and cid not in client_ids:
            errors.append(f"Project {proj['project_id']} references non-existent client {cid}")

    # Clients -> Projects (via engagements)
    for client in clients:
        for eng in client.get("engagements", []):
            pid = eng.get("project_id")
            if pid and pid not in proj_ids:
                errors.append(f"Client {client['client_id']} references non-existent project {pid}")

    # Tech stack -> Projects
    for tech in tech_stack:
        for pid in tech.get("projects", []):
            if pid not in proj_ids:
                errors.append(f"Tech {tech['tech_id']} references non-existent project {pid}")

    # Tech stack -> CVs
    for tech in tech_stack:
        for cid in tech.get("cvs", []):
            if cid not in cv_ids:
                errors.append(f"Tech {tech['tech_id']} references non-existent CV {cid}")

    # Required fields
    for cv in cvs:
        if not cv.get("cv_id"):
            errors.append("CV missing cv_id")
        if not cv.get("name"):
            errors.append(f"CV {cv.get('cv_id')} missing name")
        if not cv.get("skills"):
            warnings.append(f"CV {cv.get('cv_id')} has no skills")

    for proj in projects:
        if not proj.get("project_id"):
            errors.append("Project missing project_id")
        if not proj.get("name"):
            errors.append(f"Project {proj.get('project_id')} missing name")

    for client in clients:
        if not client.get("client_id"):
            errors.append("Client missing client_id")
        if not client.get("name"):
            errors.append(f"Client {client.get('client_id')} missing name")

    for tech in tech_stack:
        if not tech.get("tech_id"):
            errors.append("Tech missing tech_id")
        if not tech.get("name"):
            errors.append(f"Tech {tech.get('tech_id')} missing name")

    # Report
    print("=" * 60)
    print("DATA VALIDATION REPORT")
    print("=" * 60)
    print(f"CVs: {len(cvs)}")
    print(f"Projects: {len(projects)}")
    print(f"Clients: {len(clients)}")
    print(f"Tech stack: {len(tech_stack)}")
    print()

    if errors:
        print(f"ERRORS ({len(errors)}):")
        for e in errors:
            print(f"  [FAIL] {e}")
    else:
        print("[OK] No errors found")

    if warnings:
        print(f"\nWARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  [WARN] {w}")

    print()

    if errors:
        print("VALIDATION FAILED")
        return 1
    else:
        print("VALIDATION PASSED")
        return 0


if __name__ == "__main__":
    sys.exit(validate())
