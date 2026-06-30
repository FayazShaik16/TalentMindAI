import re
from datetime import date
from typing import Any, Dict, List
from app.schemas.candidate import CandidateProfile, ExperienceDetail
from app.services.extractor import parse_date

class DomainAnalyzer:
    """
    Identifies candidate's industry vertical experience across key domains (FinTech, SaaS, AI, Blockchain, etc.)
    and calculates duration of exposure and confidence scores.
    """

    DOMAINS_KWS = {
        "FinTech": ["finance", "payment", "bank", "trading", "crypto", "blockchain", "transaction", "ledger", "wealth", "fintech", "insurance"],
        "HealthTech": ["healthcare", "medical", "patient", "clinical", "hospital", "healthtech", "health", "pharma"],
        "EdTech": ["education", "student", "learning", "classroom", "school", "university", "course", "edtech"],
        "AI": ["machine learning", "deep learning", "nlp", "llm", "artificial intelligence", "computer vision", "neural network", "ai", "openai", "pytorch", "tensorflow"],
        "Cybersecurity": ["security", "penetration", "cybersecurity", "encryption", "firewall", "vulnerability", "auth", "cryptography", "owasp", "iam"],
        "Blockchain": ["blockchain", "ethereum", "bitcoin", "solidity", "smart contract", "web3", "dapp", "hyperledger"],
        "IoT": ["iot", "sensor", "hardware", "embedded", "raspberry", "arduino", "telemetry", "smart home"],
        "Cloud": ["cloud", "aws", "gcp", "azure", "kubernetes", "docker", "serverless", "devops", "cloud native"],
        "SaaS": ["saas", "software as a service", "subscription", "b2b", "multi-tenant"],
        "Gaming": ["game", "unity", "unreal", "gaming", "rendering", "physics engine", "playstation", "xbox"],
        "E-commerce": ["e-commerce", "shopify", "cart", "payment gateway", "checkout", "retail", "magento", "store"],
        "Enterprise Software": ["enterprise", "b2b", "crm", "erp", "sap", "oracle", "large-scale systems"],
        "Government": ["government", "defense", "public sector", "agency", "federal"],
        "Telecommunications": ["telecommunication", "telecom", "network", "5g", "lte", "sip", "voip", "carrier"]
    }

    def _get_exp_duration_years(self, exp: ExperienceDetail) -> float:
        s_date = parse_date(exp.start_date)
        e_date = parse_date(exp.end_date) or date.today()
        if not s_date:
            return 1.0
        delta_months = (e_date.year - s_date.year) * 12 + (e_date.month - s_date.month)
        return max(3.0, float(delta_months)) / 12.0

    def analyze(self, profile: CandidateProfile) -> Dict[str, Any]:
        detected_domains = {}

        for domain, keywords in self.DOMAINS_KWS.items():
            duration_years = 0.0
            evidence_snippets = []
            mentions_count = 0

            # Scan experiences
            for exp in profile.experiences:
                exp_text = f"{exp.job_title} {exp.description or ''}".lower()
                matched_kws = [kw for kw in keywords if re.search(r"\b" + re.escape(kw) + r"\b", exp_text)]
                if matched_kws:
                    dur = self._get_exp_duration_years(exp)
                    duration_years += dur
                    mentions_count += len(matched_kws)
                    evidence_snippets.append(
                        f"Experience at {exp.company_name} ({exp.job_title}): matched keywords {', '.join(matched_kws)}"
                    )

            # Scan projects
            for p in profile.projects:
                proj_text = f"{p.name} {p.description or ''} {' '.join(p.responsibilities)}".lower()
                matched_kws = [kw for kw in keywords if re.search(r"\b" + re.escape(kw) + r"\b", proj_text)]
                if matched_kws or (p.domain and re.search(r"\b" + re.escape(p.domain.lower()) + r"\b", domain.lower())):
                    dur = (p.duration_months or 6) / 12.0
                    duration_years += dur
                    mentions_count += len(matched_kws) if matched_kws else 1
                    evidence_snippets.append(
                        f"Project '{p.name}': matched domain/keywords"
                    )

            if duration_years > 0.0 or mentions_count > 0:
                duration_years = round(duration_years, 1)
                
                # Determine confidence & level
                if duration_years >= 2.0 and mentions_count >= 3:
                    level = "Expert / Dominant"
                    score = 0.95
                    confidence = 0.93
                elif duration_years >= 0.5 or mentions_count >= 1:
                    level = "Intermediate / Competent"
                    score = 0.75
                    confidence = 0.82
                else:
                    level = "Beginner / Exposed"
                    score = 0.40
                    confidence = 0.60

                detected_domains[domain] = {
                    "domain": domain,
                    "exposure_years": float(duration_years),
                    "proficiency_level": level,
                    "score": float(score),
                    "confidence_score": float(confidence),
                    "mentions_count": int(mentions_count),
                    "evidence": list(set(evidence_snippets))
                }

        # Filter out empty/undetected domains from main exposure dictionary
        return {
            "detected_domains": detected_domains,
            "overall_diversity_score": float(len(detected_domains) / len(self.DOMAINS_KWS))
        }

domain_analyzer = DomainAnalyzer()
