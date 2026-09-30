"""
Multi-Agent Proposal & Commercial Estimation Generator.

Orchestrates 3 specialized agents to synthesize a commercial & technical proposal:
1. Solutions Architect Agent: Formulates technical architecture & tech stack
2. Project Delivery Manager Agent: Designs step-by-step realization phases & duration
3. Financial Estimation Agent: Calculates person-days, applies TND rate card, contingency

Outputs a structured ProposalDeckData object ready for python-pptx compilation.
Supports both Groq LLM agentic synthesis and robust offline rule-based fallback.
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# --- Default Tunisian Dinar (TND) Rate Card per Day (Jours-Homme) ---
DEFAULT_RATE_CARD = {
    "Lead Solutions Architect": 850.0,
    "Senior Full-Stack Engineer": 650.0,
    "Cloud & DevOps Specialist": 700.0,
    "QA & Test Automation Engineer": 550.0,
    "Agile Project Manager (PMP/Scrum)": 600.0,
}

# Default Contingency Buffer (Risk & scope fluctuation)
DEFAULT_CONTINGENCY_PERCENT = 12.0


# --- Data Models (Pydantic v2) ---

class RoleEstimate(BaseModel):
    role: str
    rate_per_day_tnd: float
    days: int
    total_tnd: float


class PricingBreakdown(BaseModel):
    roles: List[RoleEstimate] = Field(default_factory=list)
    base_cost_tnd: float = 0.0
    contingency_percent: float = DEFAULT_CONTINGENCY_PERCENT
    contingency_tnd: float = 0.0
    total_price_tnd: float = 0.0
    maintenance_sla_annual_tnd: float = 0.0


class ProjectPhase(BaseModel):
    phase_num: int
    name: str
    duration_weeks: int
    deliverables: List[str] = Field(default_factory=list)
    key_activities: List[str] = Field(default_factory=list)


class TechnicalSolution(BaseModel):
    solution_title: str
    architecture_style: str
    summary: str
    tech_stack: Dict[str, List[str]] = Field(default_factory=dict)
    key_features: List[str] = Field(default_factory=list)
    security_compliance: List[str] = Field(default_factory=list)


class StaffingProfile(BaseModel):
    cv_id: str
    name: str
    title: str
    matched_skills: List[str] = Field(default_factory=list)
    role_in_project: str = "Core Engineer"


class RiskMitigation(BaseModel):
    risk: str
    mitigation: str


class ProposalDeckData(BaseModel):
    tender_id: str
    tender_title: str
    client_name: str
    fit_score: float
    total_duration_weeks: int
    pricing: PricingBreakdown
    technical_solution: TechnicalSolution
    phases: List[ProjectPhase] = Field(default_factory=list)
    staffing: List[StaffingProfile] = Field(default_factory=list)
    business_objectives: List[str] = Field(default_factory=list)
    client_pain_points: List[str] = Field(default_factory=list)
    risk_mitigations: List[RiskMitigation] = Field(default_factory=list)
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# --- Deterministic Offline Multi-Agent Generator ---

def _build_offline_proposal(
    tender_id: str,
    title: str,
    client: str,
    requirements: List[Dict[str, Any]],
    staffing_matches: List[Dict[str, Any]],
    fit_score: float,
) -> ProposalDeckData:
    """Deterministic, domain-grounded synthesis of technical solution, timeline & TND pricing."""
    req_texts = [r.get("text", "") for r in requirements]
    all_text = (title + " " + " ".join(req_texts)).lower()

    # Collect tech keywords
    tech_keywords = set()
    for r in requirements:
        for kw in r.get("tech_keywords", []):
            tech_keywords.add(kw.lower())

    # --- 1. Solutions Architect Agent ---
    if any(k in all_text for k in ["bancaire", "microservices", "spring", "api"]):
        arch_style = "Architecture Microservices Distribuée & Cloud-Native"
        tech_stack = {
            "Backend": ["Java 21", "Spring Boot 3.3", "Spring Cloud Gateway", "Kafka"],
            "Frontend": ["React 18", "TypeScript", "TailwindCSS"],
            "Base de données": ["PostgreSQL 16", "Redis Cluster"],
            "DevOps / Cloud": ["Docker", "Kubernetes", "GitLab CI/CD", "Prometheus"],
            "Sécurité": ["Keycloak (OAuth2 / OIDC)", "mTLS", "HashiCorp Vault"],
        }
        features = [
            "Découplage haute disponibilité via API Gateway et Service Mesh",
            "Traitement temps réel événementiel et résilience bancaire",
            "Observabilité complète (Tracing OpenTelemetry, Métriques, Logs)",
            "Chiffrement de bout en bout et conformité PCI-DSS / RGPD",
        ]
    elif any(k in all_text for k in ["sap", "erp", "s/4hana"]):
        arch_style = "Intégration d'Entreprise SAP S/4HANA & Extensions Cloud"
        tech_stack = {
            "ERP Core": ["SAP S/4HANA Cloud / On-Premise", "ABAP RESTful Application"],
            "Intégration": ["SAP Integration Suite (BTP)", "OData APIs", "RFC / BAPI"],
            "Frontend / Fiori": ["SAP Fiori Elements", "SAPUI5"],
            "Base de données": ["SAP HANA In-Memory DB"],
            "Sécurité": ["SAP Identity Authentication", "SSO SAML 2.0"],
        }
        features = [
            "Standardisation des processus financiers et logistiques clés",
            "Connecteurs sécurisés vers les applications satellites métier",
            "Expérience utilisateur moderne multi-devices via Fiori",
            "Reporting analytique temps réel sur SAP HANA",
        ]
    elif any(k in all_text for k in ["données", "data", "bi", "analytics", "santé"]):
        arch_style = "Plateforme Moderne de Données & Analytics Décisionnel"
        tech_stack = {
            "Pipeline ETL": ["Apache Airflow", "Python Fastparquet", "dbt"],
            "Stockage": ["PostgreSQL Lakehouse", "MinIO Object Storage"],
            "Visualisation": ["Power BI Embedded", "Superset", "React Dashboards"],
            "Infrastructure": ["Docker Swarm / K8s", "Linux Debian Hardened"],
            "Gouvernance": ["Anonymisation des données de santé", "Audit Trails"],
        }
        features = [
            "Ingestion automatisée et sécurisée de flux de données hétérogènes",
            "Moteur de modélisation dimensionnelle et KPI analytiques",
            "Tableaux de bord interactifs pour la direction et les opérationnels",
            "Traçabilité stricte et conformité réglementaire des accès",
        ]
    elif any(k in all_text for k in ["mobile", "transport", "citoyen", "portail"]):
        arch_style = "Portail Web Réactif & Applications Mobiles Cross-Platform"
        tech_stack = {
            "Mobile & Web": ["Flutter 3.x", "React 18", "Next.js"],
            "Backend API": ["Node.js / NestJS", "Express REST / GraphQL"],
            "Base de données": ["PostgreSQL", "PostGIS (Cartographie / Géoloc)", "Redis"],
            "Cloud & Notifications": ["Docker", "Nginx", "Firebase Cloud Messaging"],
            "Sécurité": ["Authentification JWT", "Chiffrement AES-256"],
        }
        features = [
            "Interface citoyenne ergonomique et accessible multi-supports",
            "Moteur cartographique et suivi géolocalisé temps réel",
            "Module de notification push instantanée et formulaires dématérialisés",
            "Performances optimisées pour montées en charge simultanées",
        ]
    else:
        arch_style = "Architecture Web Moderne Modulaire & API-First"
        tech_stack = {
            "Backend": ["Python FastAPI / Django", "Node.js"],
            "Frontend": ["React", "TypeScript", "TailwindCSS"],
            "Base de données": ["PostgreSQL", "Redis Cache"],
            "Infrastructure": ["Docker", "Linux Ubuntu Server", "CI/CD GitHub Actions"],
            "Sécurité": ["OAuth2 / JWT", "HTTPS / SSL", "Contrôles OWASP"],
        }
        features = [
            "Architecture modulaire favorisant l'évolutivité fonctionnelle",
            "APIs RESTful documentées via Swagger / OpenAPI",
            "Interface intuitive centrée sur l'expérience utilisateur",
            "Tests unitaires et d'intégration automatisés",
        ]

    technical_solution = TechnicalSolution(
        solution_title=f"Solution OliveSoft : {title}",
        architecture_style=arch_style,
        summary=(
            f"OliveSoft propose une solution robuste, scalable et hautement disponible, "
            f"fondée sur une {arch_style}. Notre approche garantit une intégration fluide, "
            f"une sécurité sans compromis et un transfert de compétences complet."
        ),
        tech_stack=tech_stack,
        key_features=features,
        security_compliance=[
            "Chiffrement TLS 1.3 en transit et AES-256 au repos",
            "Authentification forte et gestion fine des habilitations (RBAC)",
            "Conformité aux meilleures pratiques OWASP Top 10",
            "Sauvegardes automatisées quotidiennes et plan de reprise d'activité (PRA)",
        ],
    )

    # --- 2. Project Delivery Manager Agent ---
    req_count = max(len(requirements), 2)
    # Estimate total duration based on requirement complexity (typically 12 to 24 weeks)
    if req_count <= 3:
        total_weeks = 14
        phase_durations = [2, 6, 3, 2, 1]
    elif req_count <= 6:
        total_weeks = 18
        phase_durations = [3, 8, 4, 2, 1]
    else:
        total_weeks = 22
        phase_durations = [3, 10, 5, 3, 1]

    phases = [
        ProjectPhase(
            phase_num=1,
            name="Cadrage, Architecture & Inception",
            duration_weeks=phase_durations[0],
            deliverables=[
                "Dossier d'Architecture Technique (DAT)",
                "Spécifications Fonctionnelles Détaillées (SFD)",
                "Charte graphique et maquettes UX/UI validées",
                "Environnements de développement et CI/CD configurés",
            ],
            key_activities=[
                "Ateliers d'alignement avec les parties prenantes métier",
                "Validation des flux de données et des protocoles de sécurité",
                "Mise en place du référentiel Git et des pipelines de déploiement",
            ],
        ),
        ProjectPhase(
            phase_num=2,
            name="Développement Sprints & Core Build",
            duration_weeks=phase_durations[1],
            deliverables=[
                "Modules applicatifs core testés en continu",
                "Releases itératives bi-hebdomadaires (Démos Sprint)",
                "APIs documentées et interconnectées",
                "Rapports de couverture de tests (> 80%)",
            ],
            key_activities=[
                "Sprints Agiles de 2 semaines avec Scrum Master",
                "Revue de code systématique par l'Architecte Lead",
                "Intégration continue automatisée à chaque commit",
            ],
        ),
        ProjectPhase(
            phase_num=3,
            name="Intégration, Migration & Recette QA",
            duration_weeks=phase_durations[2],
            deliverables=[
                "Rapport d'audit de sécurité et pentest interne",
                "Rapport de tests de charge et performance",
                "Scripts de migration des données validés",
                "Environnement de pré-production conforme",
            ],
            key_activities=[
                "Tests end-to-end automatisés et validation de conformité",
                "Tests de montée en charge simulée sous stress",
                "Migration à blanc des jeux de données réels",
            ],
        ),
        ProjectPhase(
            phase_num=4,
            name="Recette Utilisateur (UAT) & Pilote",
            duration_weeks=phase_durations[3],
            deliverables=[
                "Procès-Verbal (PV) de recette provisoire signé",
                "Guides utilisateurs et manuels d'administration",
                "Programme de formation des administrateurs et utilisateurs",
            ],
            key_activities=[
                "Accompagnement quotidien des équipes métiers lors de la recette",
                "Correction prioritaire des anomalies résiduelles (SLA 24h)",
                "Sessions de formation interactives et transfert de compétences",
            ],
        ),
        ProjectPhase(
            phase_num=5,
            name="Mise en Production & Hypercare",
            duration_weeks=phase_durations[4],
            deliverables=[
                "Bascule en production (Go-Live) sans interruption de service",
                "Procès-Verbal de recette définitive",
                "Plan de maintenance préventive et corrective (SLA)",
            ],
            key_activities=[
                "Déploiement supervisé 24/7 en environnement de production",
                "Période de garantie et d'hypercare de 90 jours",
                "Comité de clôture de projet et passage de relais au support SLA",
            ],
        ),
    ]

    # --- 3. Financial & Estimation Agent (TND Grounding) ---
    # Work breakdown by role based on project duration and scope
    base_factor = total_weeks / 16.0
    role_days = [
        ("Lead Solutions Architect", DEFAULT_RATE_CARD["Lead Solutions Architect"], int(round(18 * base_factor))),
        ("Senior Full-Stack Engineer", DEFAULT_RATE_CARD["Senior Full-Stack Engineer"], int(round(55 * base_factor))),
        ("Cloud & DevOps Specialist", DEFAULT_RATE_CARD["Cloud & DevOps Specialist"], int(round(16 * base_factor))),
        ("QA & Test Automation Engineer", DEFAULT_RATE_CARD["QA & Test Automation Engineer"], int(round(15 * base_factor))),
        ("Agile Project Manager (PMP/Scrum)", DEFAULT_RATE_CARD["Agile Project Manager (PMP/Scrum)"], int(round(14 * base_factor))),
    ]

    role_estimates = []
    base_cost = 0.0
    for role_name, rate, days in role_days:
        total_role = round(rate * days, 2)
        base_cost += total_role
        role_estimates.append(
            RoleEstimate(
                role=role_name,
                rate_per_day_tnd=rate,
                days=days,
                total_tnd=total_role,
            )
        )

    contingency = round(base_cost * (DEFAULT_CONTINGENCY_PERCENT / 100.0), 2)
    total_price = round(base_cost + contingency, 2)
    maintenance_sla = round(total_price * 0.15, 2)  # 15% annual SLA

    pricing = PricingBreakdown(
        roles=role_estimates,
        base_cost_tnd=round(base_cost, 2),
        contingency_percent=DEFAULT_CONTINGENCY_PERCENT,
        contingency_tnd=contingency,
        total_price_tnd=total_price,
        maintenance_sla_annual_tnd=maintenance_sla,
    )

    # --- 4. Staffing Extraction ---
    staffing_list = []
    for s in staffing_matches[:4]:
        staffing_list.append(
            StaffingProfile(
                cv_id=s.get("cv_id", "CV-001"),
                name=s.get("name", "Consultant OliveSoft"),
                title=s.get("title", "Ingénieur d'Études"),
                matched_skills=s.get("skills_matched", []),
                role_in_project=s.get("title", "Consultant Expert"),
            )
        )

    # Default fallback if no CV matches provided
    if not staffing_list:
        staffing_list = [
            StaffingProfile(
                cv_id="CV-003",
                name="Mohamed Kacem",
                title="Lead Solutions Architect",
                matched_skills=["Spring Boot", "Microservices", "Kubernetes"],
                role_in_project="Directeur Technique & Architecte",
            ),
            StaffingProfile(
                cv_id="CV-001",
                name="Ahmed Ben Ali",
                title="Senior Full-Stack Engineer",
                matched_skills=["React", "Java", "Docker", "PostgreSQL"],
                role_in_project="Tech Lead Développement",
            ),
            StaffingProfile(
                cv_id="CV-008",
                name="Karim Mansour",
                title="Cloud & DevOps Engineer",
                matched_skills=["CI/CD", "Docker", "Kubernetes", "Linux"],
                role_in_project="Responsable Infrastructure & Déploiement",
            ),
        ]

    # --- 5. Business & Risk Context ---
    business_objectives = [
        f"Moderniser le système d'information de {client} selon les standards de l'industrie",
        "Garantir une haute disponibilité et une scalabilité face aux montées en charge",
        "Réduire les coûts d'exploitation et optimiser les temps de réponse utilisateurs",
        "Assurer la souveraineté et la conformité stricte des données hébergées",
    ]

    pain_points = [
        "Systèmes existants hétérogènes ou monolithiques limitant l'évolutivité métier",
        "Processus manuels chronophages et risques accrus d'erreurs de saisie",
        "Manque de visibilité analytique et de reporting en temps réel",
        "Exigences de sécurité et de résilience réglementaires renforcées",
    ]

    risk_mitigations = [
        RiskMitigation(
            risk="Complexité d'intégration avec l'infrastructure et les bases existantes",
            mitigation="Phase de cadrage approfondie (Phase 1) avec cartographie détaillée des interfaces et tests de connecteurs préliminaires.",
        ),
        RiskMitigation(
            risk="Glissement de périmètre fonctionnel en cours de projet",
            mitigation="Gestion agile en sprints de 2 semaines avec backlog priorisé, arbitrage hebdomadaire et suivi strict par le Scrum Master.",
        ),
        RiskMitigation(
            risk="Indisponibilité des utilisateurs clés pour la recette UAT",
            mitigation="Planification anticipée des sessions de recette, mise à disposition de jeux de données préparés et guides pas-à-pas.",
        ),
        RiskMitigation(
            risk="Continuité de service lors de la mise en production",
            mitigation="Déploiement en mode Blue/Green ou Canari avec rollback automatisé et astreinte technique 24/7 durant l'hypercare.",
        ),
    ]

    return ProposalDeckData(
        tender_id=tender_id,
        tender_title=title,
        client_name=client,
        fit_score=fit_score,
        total_duration_weeks=total_weeks,
        pricing=pricing,
        technical_solution=technical_solution,
        phases=phases,
        staffing=staffing_list,
        business_objectives=business_objectives,
        client_pain_points=pain_points,
        risk_mitigations=risk_mitigations,
    )


# --- Multi-Agent Orchestrator ---

def generate_proposal_deck_data(
    tender_id: str,
    title: str,
    client: Optional[str] = None,
    requirements: Optional[List[Dict[str, Any]]] = None,
    staffing_matches: Optional[List[Dict[str, Any]]] = None,
    fit_score: float = 1.0,
) -> ProposalDeckData:
    """
    Main entry point: Generates a complete proposal deck dataset.
    Uses Groq LLM if GROQ_API_KEY is available; seamlessly falls back to
    deterministic rule-based multi-agent synthesizer.
    """
    client_name = client or "L'Organisme Contractant"
    reqs = requirements or []
    staffing = staffing_matches or []

    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        try:
            from openai import OpenAI

            client_ai = OpenAI(api_key=groq_key, base_url="https://api.groq.com/openai/v1")
            model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

            system_prompt = (
                "You are an executive proposal engineering team for OliveSoft (a premier Tunisian software & systems engineering firm). "
                "Synthesize a complete commercial proposal in JSON format. "
                "Currency MUST be Tunisian Dinars (TND). "
                "Return a valid JSON object matching the ProposalDeckData structure."
            )

            user_prompt = f"""
Tender ID: {tender_id}
Tender Title: {title}
Client: {client_name}
Fit Score: {fit_score}
Requirements: {json.dumps(reqs, ensure_ascii=False)}
Staffing Candidates: {json.dumps(staffing, ensure_ascii=False)}

Generate a comprehensive proposal with:
1. Technical architecture and tech stack
2. 5-phase realization plan with durations and deliverables
3. Pricing breakdown in TND with person-days per role (Architect 850, Senior Dev 650, DevOps 700, QA 550, PM 600)
4. Business context, pain points and 4 key risk mitigations.
"""

            response = client_ai.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
                max_tokens=2500,
            )

            raw_json = response.choices[0].message.content
            parsed = json.loads(raw_json)
            # Validate and construct
            return ProposalDeckData(**parsed)

        except Exception as e:
            logger.warning("Groq agentic proposal generation failed, falling back to deterministic engine: %s", e)

    # Deterministic fallback (always succeeds, zero downtime, instant execution)
    return _build_offline_proposal(
        tender_id=tender_id,
        title=title,
        client=client_name,
        requirements=reqs,
        staffing_matches=staffing,
        fit_score=fit_score,
    )
