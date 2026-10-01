"""
Pre-packaged dataset and helper functions for the OliveSoft Executive Sales Dashboard.
Provides benchmark tenders, prospect dossiers, coverage matrices, and proposal data.
"""

from typing import Any, Dict, List

BENCHMARK_TENDERS: List[Dict[str, Any]] = [
    {
        "tender_id": "AO-2026-TN-042",
        "title": "Mise en place d'un système national d'information hospitalier et dossiers médicaux partagés",
        "buyer": "Ministère de la Santé",
        "sector": "Santé Publique & Hôpitaux",
        "country": "Tunisie",
        "source": "appeloffres.com",
        "publication_date": "2026-09-24",
        "submission_deadline": "2026-11-15",
        "budget_scale": "450,000 - 650,000 TND",
        "status": "QUALIFIED",
        "fit_score": 0.92,
        "is_qualified": True,
        "description": "Mise en place d'un système national d'information hospitalier (SIH) et dossiers médicaux partagés (DMP) pour les établissements publics de santé. Lot 1: Dossier Patient Informatisé (DPI) et interopérabilité HL7/FHIR. Lot 2: Portail praticiens et portail patient sécurisé (SSO, RGPD). Lot 3: Infrastructure cloud hybride et haute disponibilité. Lot 4: Accompagnement au changement et formation des équipes soignantes.",
        "prospect_profile": {
            "buyer_name": "Ministère de la Santé",
            "sector": "Santé Publique",
            "estimated_budget_tnd": "550,000 TND",
            "strategic_goals": [
                "Modernisation et interopérabilité des 24 hôpitaux régionaux",
                "Dossier médical partagé unique par citoyen conforme HL7/FHIR",
                "Réduction des délais de prise en charge et traçabilité médicale"
            ],
            "pain_points": [
                "Dossiers papier dispersés et pertes de données patient",
                "Absence de connectivité temps réel entre dispensaires et hôpitaux",
                "Contraintes strictes de souveraineté et sécurité des données de santé"
            ],
            "key_partners": ["CNAM", "Hôpitaux Universitaires", "Ministère des Technologies"],
            "procurement_criteria": "40% Méthodologie & Architecture, 30% Références similaires, 30% Offre Financière"
        },
        "requirements": [
            {
                "req_id": "REQ-SANTE-01",
                "text": "Conception et déploiement du Dossier Patient Informatisé avec interopérabilité HL7/FHIR",
                "status": "covered",
                "matched_cv": "Sami Ben Salah (Senior Healthcare Systems Architect)",
                "matched_project": "Plateforme Télésanté & Suivi Clinique (Ministère de la Santé)",
                "matched_tech": "FHIR Server, Docker, PostgreSQL"
            },
            {
                "req_id": "REQ-SANTE-02",
                "text": "Développement des portails web et mobiles praticiens et patients avec authentification SSO",
                "status": "covered",
                "matched_cv": "Yassine Mansour (Lead Full-Stack Web/Mobile)",
                "matched_project": "Portail Citoyen e-Gov (Ministère des Technologies)",
                "matched_tech": "React, Node.js, Keycloak SSO"
            },
            {
                "req_id": "REQ-SANTE-03",
                "text": "Architecture microservices résiliente et conteneurisation Docker / Kubernetes",
                "status": "covered",
                "matched_cv": "Karim Bouazizi (DevOps & Cloud Architect)",
                "matched_project": "Core Banking Microservices Migration (BIAT)",
                "matched_tech": "Kubernetes, Helm, Istio Service Mesh"
            },
            {
                "req_id": "REQ-SANTE-04",
                "text": "Sécurité, conformité RGPD santé et chiffrement des données de bout en bout",
                "status": "covered",
                "matched_cv": "Ines Triki (Cybersecurity & Data Privacy Lead)",
                "matched_project": "Audit Sécurité & Chiffrement ISO 27001 (Banque Centrale)",
                "matched_tech": "Vault, mTLS, AES-256"
            }
        ],
        "staffing": [
            {
                "name": "Sami Ben Salah",
                "role": "Lead Healthcare Solutions Architect",
                "seniority": "12 ans d'expérience",
                "match_rate": "98%",
                "skills": ["HL7/FHIR", "Architecture SIH", "Spring Boot", "PostgreSQL"]
            },
            {
                "name": "Yassine Mansour",
                "role": "Senior Full-Stack Engineer",
                "seniority": "7 ans d'expérience",
                "match_rate": "94%",
                "skills": ["React", "Node.js", "Keycloak SSO", "APIs REST"]
            },
            {
                "name": "Karim Bouazizi",
                "role": "DevOps & Cloud Specialist",
                "seniority": "8 ans d'expérience",
                "match_rate": "92%",
                "skills": ["Kubernetes", "Docker", "CI/CD GitLab", "Monitoring Prometheus"]
            },
            {
                "name": "Ines Triki",
                "role": "Lead Sécurité & Conformité",
                "seniority": "9 ans d'expérience",
                "match_rate": "95%",
                "skills": ["ISO 27001", "RGPD Santé", "Audit Sécurité", "Chiffrement"]
            }
        ],
        "commercial": {
            "total_price_tnd": 158400.0,
            "duration_weeks": 22,
            "phases_count": 5,
            "rate_daily_avg": "680 TND/jour",
            "file_name": "AO-2026-TN-042_OliveSoft_Proposal.pptx"
        }
    },
    {
        "tender_id": "TENDER-003",
        "title": "Migration du système bancaire vers une architecture microservices",
        "buyer": "Banque Internationale Arabe de Tunisie (BIAT)",
        "sector": "Banque & Fintech",
        "country": "Tunisie",
        "source": "appeloffres.com",
        "publication_date": "2026-09-18",
        "submission_deadline": "2026-10-25",
        "budget_scale": "380,000 - 520,000 TND",
        "status": "QUALIFIED",
        "fit_score": 0.95,
        "is_qualified": True,
        "description": "Migration du système d'information bancaire existant vers une architecture microservices. Lot 1: Audit et conception de l'architecture cible. Lot 2: Développement des services core banking (gestion des comptes, virements). Lot 3: Migration des données depuis legacy Oracle Forms. Lot 4: Tests de performance et sécurité.",
        "prospect_profile": {
            "buyer_name": "Banque Internationale Arabe de Tunisie",
            "sector": "Banque de Détail & Corporate",
            "estimated_budget_tnd": "450,000 TND",
            "strategic_goals": [
                "Découplage du mainframe legacy Oracle Forms vers microservices agiles",
                "Exposition d'APIs Open Banking conformes BCT",
                "Temps de réponse inférieur à 80ms sur les opérations transactionnelles"
            ],
            "pain_points": [
                "Dette technique sur l'ERP bancaire legacy",
                "Dépendance critique aux requêtes PL/SQL non documentées",
                "Fenêtres de maintenance trop contraignantes"
            ],
            "key_partners": ["Banque Centrale de Tunisie", "Monétique Tunisie"],
            "procurement_criteria": "50% Expertise Technique & Références Bancaires, 30% Équipe, 20% Coût"
        },
        "requirements": [
            {
                "req_id": "REQ-01",
                "text": "Audit et conception de l'architecture cible microservices, API Gateway et orchestrateur",
                "status": "covered",
                "matched_cv": "Slim Ammar (Senior Java/Spring Boot Architect)",
                "matched_project": "Core Banking Microservices Migration (BIAT)",
                "matched_tech": "Spring Cloud, Spring Boot, API Gateway"
            },
            {
                "req_id": "REQ-02",
                "text": "Développement des services core banking (comptes, virements, opérations)",
                "status": "covered",
                "matched_cv": "Nader Trabelsi (Senior Backend Java/Kotlin)",
                "matched_project": "Core Banking Microservices Migration",
                "matched_tech": "Java 17, Spring Boot, Kafka"
            },
            {
                "req_id": "REQ-03",
                "text": "Migration des données depuis le système legacy Oracle Forms",
                "status": "covered",
                "matched_cv": "Mouna Gharbi (Database & Data Migration Specialist)",
                "matched_project": "Data Migration & ETL Bancaire",
                "matched_tech": "Oracle, Liquibase, Apache NiFi"
            },
            {
                "req_id": "REQ-04",
                "text": "Tests de performance et conformité sécurité bancaire",
                "status": "covered",
                "matched_cv": "Mehdi Chaabane (QA Automation & Performance Engineer)",
                "matched_project": "Audit Sécurité & Stress Test Bancaire",
                "matched_tech": "JMeter, OWASP ZAP, SonarQube"
            }
        ],
        "staffing": [
            {
                "name": "Slim Ammar",
                "role": "Lead Banking Architect",
                "seniority": "14 ans d'expérience",
                "match_rate": "99%",
                "skills": ["Spring Cloud", "Core Banking", "Kafka", "Microservices"]
            },
            {
                "name": "Nader Trabelsi",
                "role": "Senior Java Backend Engineer",
                "seniority": "8 ans d'expérience",
                "match_rate": "95%",
                "skills": ["Java 17", "Spring Boot", "APIs REST", "Oracle"]
            },
            {
                "name": "Mouna Gharbi",
                "role": "Data Migration Lead",
                "seniority": "10 ans d'expérience",
                "match_rate": "92%",
                "skills": ["Oracle DB", "ETL Pipelines", "PL/SQL", "PostgreSQL"]
            }
        ],
        "commercial": {
            "total_price_tnd": 142800.0,
            "duration_weeks": 20,
            "phases_count": 5,
            "rate_daily_avg": "710 TND/jour",
            "file_name": "TENDER-003_OliveSoft_Proposal.pptx"
        }
    },
    {
        "tender_id": "TENDER-002",
        "title": "Développement d'un portail web citoyen pour les services publics",
        "buyer": "Ministère des Technologies de la Communication",
        "sector": "e-Gouvernement & Administration",
        "country": "Tunisie",
        "source": "appeloffres.com",
        "publication_date": "2026-09-20",
        "submission_deadline": "2026-11-01",
        "budget_scale": "280,000 - 420,000 TND",
        "status": "QUALIFIED",
        "fit_score": 0.89,
        "is_qualified": True,
        "description": "Conception et développement d'un portail web de services en ligne pour les citoyens: authentification sécurisée, gestion des démarches, paiement en ligne, responsive mobile. Technologies attendues: framework moderne, base relationnelle, API REST.",
        "prospect_profile": {
            "buyer_name": "Ministère des Technologies de la Communication",
            "sector": "Secteur Public",
            "estimated_budget_tnd": "350,000 TND",
            "strategic_goals": [
                "Digitalisation à 100% des 50 démarches administratives prioritaires",
                "Expérience citoyenne fluide et accessible sur smartphone (PWA)",
                "Intégration de la passerelle nationale de paiement électronique"
            ],
            "pain_points": [
                "Files d'attente guichets et lenteur de traitement des dossiers",
                "Taux d'abandon élevé sur les anciens formulaires PDF"
            ],
            "key_partners": ["Centre d'Informatique du Ministère des Finances", "La Poste Tunisienne"],
            "procurement_criteria": "40% Ergonomie UX/UI, 35% Méthodologie Agile, 25% Offre Financière"
        },
        "requirements": [
            {
                "req_id": "REQ-01",
                "text": "Interface web responsive citoyenne sous React et design system accessible",
                "status": "covered",
                "matched_cv": "Yassine Mansour (Lead Full-Stack Web)",
                "matched_project": "Portail e-Gov Tunisie (MTC)",
                "matched_tech": "React, Tailwind, Accessibility WCAG 2.1"
            },
            {
                "req_id": "REQ-02",
                "text": "Authentification sécurisée citoyenne Mobile ID et SSO Keycloak",
                "status": "covered",
                "matched_cv": "Ines Triki (Security Lead)",
                "matched_project": "Portail e-Gov",
                "matched_tech": "Keycloak, OpenID Connect, OAuth2"
            },
            {
                "req_id": "REQ-03",
                "text": "Passerelle de paiement en ligne sécurisée (Monétique / Poste)",
                "status": "covered",
                "matched_cv": "Sami Ben Salah (Architect)",
                "matched_project": "Core Banking Payment Gateway",
                "matched_tech": "APIs REST, Webhooks, Chiffrement"
            }
        ],
        "staffing": [
            {
                "name": "Yassine Mansour",
                "role": "Lead Frontend / UX Architect",
                "seniority": "7 ans d'expérience",
                "match_rate": "96%",
                "skills": ["React", "Design Systems", "PWA", "TypeScript"]
            },
            {
                "name": "Nader Trabelsi",
                "role": "Backend API Developer",
                "seniority": "8 ans d'expérience",
                "match_rate": "90%",
                "skills": ["Node.js", "PostgreSQL", "Paiement API", "Docker"]
            }
        ],
        "commercial": {
            "total_price_tnd": 118500.0,
            "duration_weeks": 16,
            "phases_count": 5,
            "rate_daily_avg": "640 TND/jour",
            "file_name": "TENDER-002_OliveSoft_Proposal.pptx"
        }
    },
    {
        "tender_id": "TENDER-004",
        "title": "Mise en place d'un ERP SAP S/4HANA",
        "buyer": "Groupe Industriel Poulina",
        "sector": "Industrie & Agroalimentaire",
        "country": "Tunisie",
        "source": "appeloffres.com",
        "publication_date": "2026-09-22",
        "submission_deadline": "2026-11-05",
        "budget_scale": "550,000 - 800,000 TND",
        "status": "QUALIFIED",
        "fit_score": 0.91,
        "is_qualified": True,
        "description": "Mise en place d'un système ERP SAP S/4HANA pour un groupe industriel. Périmètre: modules Finance (FI/CO), Gestion des achats et stocks (MM), Ventes et distribution (SD). Consultants certifiés SAP exigés.",
        "prospect_profile": {
            "buyer_name": "Groupe Industriel Poulina",
            "sector": "Agro-alimentaire & Distribution",
            "estimated_budget_tnd": "680,000 TND",
            "strategic_goals": [
                "Unification de la comptabilité analytique multi-filiales sur S/4HANA",
                "Optimisation de la chaîne logistique et traçabilité en temps réel",
                "Clôtures comptables réduites de 15 jours à 3 jours"
            ],
            "pain_points": [
                "Multiplicité d'ERP hétérogènes non connectés entre usines",
                "Rapprochement manuel complexe des flux inter-compagnies"
            ],
            "key_partners": ["SAP Partner Ecosystem"],
            "procurement_criteria": "45% Certifications SAP Consultants, 35% Méthodologie de Reprise de Données, 20% Budget"
        },
        "requirements": [
            {
                "req_id": "REQ-01",
                "text": "Paramétrage et déploiement des modules SAP S/4HANA FI/CO, MM, SD",
                "status": "covered",
                "matched_cv": "Tarek Ben Amor (Consultant Senior SAP S/4HANA)",
                "matched_project": "Déploiement ERP SAP S/4HANA (Groupe Chimique)",
                "matched_tech": "SAP S/4HANA, FI/CO, MM, SD"
            },
            {
                "req_id": "REQ-02",
                "text": "Développements spécifiques ABAP Core Data Services et interfaces API",
                "status": "covered",
                "matched_cv": "Tarek Ben Amor (SAP ABAP Lead)",
                "matched_project": "Projet SAP Groupe Poulina Supply Chain",
                "matched_tech": "ABAP CDS, OData, SAP Fiori"
            },
            {
                "req_id": "REQ-03",
                "text": "Reprise des données historiques et formation des utilisateurs clés",
                "status": "covered",
                "matched_cv": "Mouna Gharbi (Data Specialist)",
                "matched_project": "Data Migration Poulina",
                "matched_tech": "SAP Migration Cockpit, Excel ETL"
            }
        ],
        "staffing": [
            {
                "name": "Tarek Ben Amor",
                "role": "Lead SAP S/4HANA Consultant",
                "seniority": "13 ans d'expérience",
                "match_rate": "98%",
                "skills": ["SAP S/4HANA", "FI/CO", "MM", "ABAP CDS", "Fiori"]
            }
        ],
        "commercial": {
            "total_price_tnd": 194000.0,
            "duration_weeks": 26,
            "phases_count": 5,
            "rate_daily_avg": "850 TND/jour",
            "file_name": "TENDER-004_OliveSoft_Proposal.pptx"
        }
    },
    {
        "tender_id": "TENDER-005",
        "title": "Développement d'une application mobile de transport public",
        "buyer": "Société des Transports de Tunis (TRANSTU)",
        "sector": "Transport & Mobilité Urbaine",
        "country": "Tunisie",
        "source": "appeloffres.com",
        "publication_date": "2026-09-25",
        "submission_deadline": "2026-11-10",
        "budget_scale": "180,000 - 300,000 TND",
        "status": "QUALIFIED",
        "fit_score": 0.88,
        "is_qualified": True,
        "description": "Développement d'une application mobile multiplateforme pour le réseau de transport public: calcul d'itinéraires, horaires temps réel, tickets dématérialisés, notifications push, intégration billettique.",
        "prospect_profile": {
            "buyer_name": "Société des Transports de Tunis",
            "sector": "Mobilité Publique",
            "estimated_budget_tnd": "240,000 TND",
            "strategic_goals": [
                "Information voyageur géolocalisée en temps réel pour 800,000 usagers/jour",
                "Mise en place de la billettique dématérialisée par QR Code"
            ],
            "pain_points": [
                "Retards non communiqués et mécontentement des usagers",
                "Fraude estimée à 18% sur les titres de transport physiques"
            ],
            "key_partners": ["Ministère du Transport"],
            "procurement_criteria": "40% Qualité UI/UX Mobile, 35% Performance GPS/Temps Réel, 25% Coût"
        },
        "requirements": [
            {
                "req_id": "REQ-01",
                "text": "Application mobile Flutter multiplateforme iOS et Android",
                "status": "covered",
                "matched_cv": "Yassine Mansour (Mobile Lead)",
                "matched_project": "Application Mobile Citoyenne",
                "matched_tech": "Flutter, Dart, Provider"
            },
            {
                "req_id": "REQ-02",
                "text": "Calcul d'itinéraire multimodal et géolocalisation bus/métro en temps réel",
                "status": "covered",
                "matched_cv": "Karim Bouazizi (Cloud/IoT)",
                "matched_project": "STEG Smart Metering IoT Pipeline",
                "matched_tech": "WebSockets, MQTT, OpenStreetMap"
            }
        ],
        "staffing": [
            {
                "name": "Yassine Mansour",
                "role": "Mobile App Lead (Flutter)",
                "seniority": "7 ans d'expérience",
                "match_rate": "93%",
                "skills": ["Flutter", "iOS", "Android", "Cartographie GPS"]
            }
        ],
        "commercial": {
            "total_price_tnd": 96500.0,
            "duration_weeks": 14,
            "phases_count": 5,
            "rate_daily_avg": "620 TND/jour",
            "file_name": "TENDER-005_OliveSoft_Proposal.pptx"
        }
    },
    {
        "tender_id": "TENDER-006",
        "title": "Audit de cybersécurité et mise en conformité ISO 27001",
        "buyer": "Institution Financière Nationale",
        "sector": "Sécurité & Audit Réglementaire",
        "country": "Tunisie",
        "source": "appeloffres.com",
        "publication_date": "2026-09-21",
        "submission_deadline": "2026-10-28",
        "budget_scale": "120,000 - 190,000 TND",
        "status": "QUALIFIED",
        "fit_score": 0.94,
        "is_qualified": True,
        "description": "Mission d'audit de cybersécurité, tests d'intrusion (pentest) web et infrastructure, revue de code, analyse des risques et plan d'alignement ISO 27001.",
        "prospect_profile": {
            "buyer_name": "Institution Financière Nationale",
            "sector": "Finance & Assurances",
            "estimated_budget_tnd": "150,000 TND",
            "strategic_goals": [
                "Conformité avec la circulaire BCT sur la cyber-résilience",
                "Certification ISO 27001 du centre de données principal"
            ],
            "pain_points": [
                "Recrudescence des tentatives de phishing et vulnérabilités sur les API partenaires"
            ],
            "key_partners": ["ANSI (Agence Nationale de la Sécurité Informatique)"],
            "procurement_criteria": "50% Accréditations Auditeurs (CEH, CISSP), 30% Méthodologie Pentest, 20% Budget"
        },
        "requirements": [
            {
                "req_id": "REQ-01",
                "text": "Audit organisationnel et technique ISO 27001 avec matrice des risques",
                "status": "covered",
                "matched_cv": "Ines Triki (Lead Auditor ISO 27001 / CISSP)",
                "matched_project": "Audit Réglementaire & Sécurité BCT",
                "matched_tech": "ISO 27001, EBIOS RM, NIST"
            },
            {
                "req_id": "REQ-02",
                "text": "Tests d'intrusion (pentest) externes et internes web/réseau",
                "status": "covered",
                "matched_cv": "Ines Triki (Ethical Hacker CEH)",
                "matched_project": "Pentest Infrastructure Bancaire",
                "matched_tech": "Burp Suite Pro, Kali, Metasploit, Nessus"
            }
        ],
        "staffing": [
            {
                "name": "Ines Triki",
                "role": "Lead Cyber Security Auditor (CISSP, CEH)",
                "seniority": "9 ans d'expérience",
                "match_rate": "97%",
                "skills": ["ISO 27001", "Pentest", "OWASP", "EBIOS RM"]
            }
        ],
        "commercial": {
            "total_price_tnd": 78000.0,
            "duration_weeks": 10,
            "phases_count": 4,
            "rate_daily_avg": "780 TND/jour",
            "file_name": "TENDER-006_OliveSoft_Proposal.pptx"
        }
    },
    {
        "tender_id": "TENDER-007",
        "title": "Plateforme Big Data & Détection de Fraude Sociale",
        "buyer": "Caisse Nationale de Sécurité Sociale (CNSS)",
        "sector": "Secteur Public & Big Data",
        "country": "Tunisie",
        "source": "appeloffres.com",
        "publication_date": "2026-09-23",
        "submission_deadline": "2026-11-12",
        "budget_scale": "350,000 - 520,000 TND",
        "status": "QUALIFIED",
        "fit_score": 0.90,
        "is_qualified": True,
        "description": "Déploiement d'un Data Lake analytique, pipelines ETL distribués, modèles de Machine Learning de détection d'anomalies et déclarations frauduleuses, et tableaux de bord décisionnels interactifs.",
        "prospect_profile": {
            "buyer_name": "Caisse Nationale de Sécurité Sociale",
            "sector": "Protection Sociale",
            "estimated_budget_tnd": "450,000 TND",
            "strategic_goals": [
                "Détection automatisée des fausses déclarations et fraudes aux cotisations",
                "Consolidation de 15 années d'historique de cotisations dans un data lake unifié"
            ],
            "pain_points": [
                "Perte annuelle estimée à plusieurs dizaines de millions de dinars par sous-déclaration",
                "Temps de calcul des bilans annuels nécessitant plusieurs semaines"
            ],
            "key_partners": ["Ministère des Affaires Sociales"],
            "procurement_criteria": "40% Performance Modèles ML, 35% Architecture Big Data, 25% Prix"
        },
        "requirements": [
            {
                "req_id": "REQ-01",
                "text": "Data Lake et pipelines ETL temps réel distribués",
                "status": "covered",
                "matched_cv": "Walid Ghorbel (Data Engineer Lead)",
                "matched_project": "Plateforme Big Data & Détection Fraude CNSS",
                "matched_tech": "Apache Spark, Airflow, Hadoop, PostgreSQL"
            },
            {
                "req_id": "REQ-02",
                "text": "Modèles prédictifs et détection d'anomalies non-supervisée",
                "status": "covered",
                "matched_cv": "Walid Ghorbel (Machine Learning Engineer)",
                "matched_project": "Plateforme CNSS",
                "matched_tech": "Scikit-Learn, PySpark, XGBoost"
            },
            {
                "req_id": "REQ-03",
                "text": "Tableaux de bord de visualisation décisionnels pour 50+ directeurs",
                "status": "covered",
                "matched_cv": "Sarra Khemir (BI & Visualization Developer)",
                "matched_project": "Tableaux de bord CNSS",
                "matched_tech": "Power BI Embedded, Superset, React"
            }
        ],
        "staffing": [
            {
                "name": "Walid Ghorbel",
                "role": "Lead Big Data / ML Engineer",
                "seniority": "9 ans d'expérience",
                "match_rate": "95%",
                "skills": ["Apache Spark", "Machine Learning", "Airflow", "Python"]
            },
            {
                "name": "Sarra Khemir",
                "role": "Senior BI & Dashboard Specialist",
                "seniority": "6 ans d'expérience",
                "match_rate": "92%",
                "skills": ["Power BI", "SQL Server", "Data Modeling", "DAX"]
            }
        ],
        "commercial": {
            "total_price_tnd": 139500.0,
            "duration_weeks": 18,
            "phases_count": 5,
            "rate_daily_avg": "670 TND/jour",
            "file_name": "TENDER-007_OliveSoft_Proposal.pptx"
        }
    },
    {
        "tender_id": "OUT-OF-SCOPE-AGRI",
        "title": "Fourniture de semences agricoles certifiées et engrais chimiques",
        "buyer": "Ministère de l'Agriculture et des Ressources Hydrauliques",
        "sector": "Agriculture & Intrants",
        "country": "Tunisie",
        "source": "appeloffres.com",
        "publication_date": "2026-09-15",
        "submission_deadline": "2026-10-15",
        "budget_scale": "150,000 TND",
        "status": "DISQUALIFIED",
        "fit_score": 0.0,
        "is_qualified": False,
        "description": "Appel d'offres pour l'acquisition de 50 tonnes de semences de blé dur sélectionnées et fertilisants NPK pour la campagne céréalière 2026-2027. Livraison dans les dépôts régionaux de Béja, Jendouba et Bizerte.",
        "prospect_profile": {
            "buyer_name": "Ministère de l'Agriculture",
            "sector": "Agriculture & Elevage",
            "estimated_budget_tnd": "150,000 TND",
            "strategic_goals": ["Approvisionnement en semences céréalières"],
            "pain_points": ["Délais de livraison stricts avant la saison des labours"],
            "key_partners": ["Office des Céréales"],
            "procurement_criteria": "100% Prix le plus bas conforme aux normes agronomiques"
        },
        "requirements": [
            {
                "req_id": "REQ-AGRI-01",
                "text": "Fourniture de 50 tonnes de blé dur certifié R1 avec taux de germination > 90%",
                "status": "not_covered",
                "matched_cv": "Aucun profil disponible (Inadéquation sectorielle)",
                "matched_project": "Aucun projet similaire dans la base IT OliveSoft",
                "matched_tech": "Aucun outil informatique applicable"
            },
            {
                "req_id": "REQ-AGRI-02",
                "text": "Livraison logistique sécurisée et stockage dans les silos régionaux",
                "status": "not_covered",
                "matched_cv": "Aucun profil disponible",
                "matched_project": "Aucun projet logistique agricole",
                "matched_tech": "N/A"
            }
        ],
        "staffing": [],
        "commercial": {
            "total_price_tnd": 0.0,
            "duration_weeks": 0,
            "phases_count": 0,
            "rate_daily_avg": "0 TND",
            "file_name": ""
        }
    }
]
