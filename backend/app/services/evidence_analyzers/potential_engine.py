from typing import Any, Dict
from app.schemas.candidate import CandidateProfile

class CandidatePotentialEngine:
    """
    Evaluates continuous learning velocity, tech adoption rate, certification frequency,
    innovation potentials, and computes confidence scores for role readiness levels (Junior to EM).
    """

    def analyze_potential(
        self,
        profile: CandidateProfile,
        career_analysis: Dict[str, Any],
        skills_verification: Dict[str, Any],
        projects_evidence: Dict[str, Any]
    ) -> Dict[str, Any]:
        features = profile.engineered_features
        experiences = profile.experiences
        projects = profile.projects
        certifications = profile.certifications

        years_exp = max(1.0, float(features.years_experience))

        # 1. Continuous Learning Velocity
        cert_count = len(certifications)
        tech_count = len(skills_verification)
        project_count = len(projects)

        adoption_speed = "Medium"
        if years_exp > 0:
            techs_per_year = tech_count / years_exp
            if techs_per_year > 2.0:
                adoption_speed = "High"
            elif techs_per_year < 0.8:
                adoption_speed = "Low"

        # Continuous Learning Score (0.0 to 1.0)
        learning_score = min(1.0, (cert_count * 0.20) + (tech_count * 0.05) + (project_count * 0.10))

        # 2. Potential Dimensions (0.0 to 1.0)
        # Adaptability
        domain_diversity = features.domain_diversity
        company_count = features.distinct_companies
        adaptability = min(1.0, (company_count * 0.12) + (domain_diversity * 0.15))

        # Innovation Potential
        innovation_hits = 0
        for p in projects:
            corpus = f"{p.name} {p.description or ''} {' '.join(p.responsibilities)}".lower()
            if any(kw in corpus for kw in ["scratch", "novel", "innovated", "architected", "patent", "optimized"]):
                innovation_hits += 1
        innovation_potential = min(1.0, 0.3 + (innovation_hits * 0.25))

        # Leadership Potential
        leadership_hits = 0
        for exp in experiences:
            desc = (exp.description or "").lower()
            if any(kw in desc for kw in ["mentor", "lead", "manage", "coach", "train", "supervise"]):
                leadership_hits += 1
        leadership_potential = min(1.0, 0.2 + (leadership_hits * 0.25))

        # Problem Solving
        has_architecture = any(s.lower() in ["system design", "architecture", "microservices"] for s in skills_verification.keys())
        problem_solving = min(1.0, 0.4 + (features.leadership_score * 0.1) + (0.2 if has_architecture else 0.0))

        # Growth Potential
        growth_potential = float(round((learning_score * 0.4 + adaptability * 0.3 + innovation_potential * 0.3), 2))

        # 3. Role Readiness Engine (0.0 to 1.0 confidence)
        junior_readiness = 1.0
        mid_readiness = min(1.0, years_exp / 3.0)
        
        # Senior readiness checks system design/cloud exposure
        has_senior_skills = any(s.lower() in ["system design", "architecture", "kubernetes", "aws", "gcp", "docker"] for s in skills_verification.keys())
        senior_readiness = min(1.0, years_exp / 5.0) * (0.9 if has_senior_skills else 0.5)

        # Lead/Arch/EM readiness checks leadership and ownership
        has_lead_skills = any(s.lower() in ["lead", "mentor", "scrum", "manage"] for s in skills_verification.keys()) or leadership_potential > 0.5
        lead_readiness = min(1.0, years_exp / 7.0) * (0.95 if has_lead_skills else 0.4)

        has_arch_skills = has_architecture or problem_solving > 0.6
        architect_readiness = min(1.0, years_exp / 8.0) * (0.95 if has_arch_skills else 0.3)

        has_em_skills = any("manager" in r.lower() or "lead" in r.lower() for r in [e.job_title for e in experiences]) or leadership_potential > 0.7
        em_readiness = min(1.0, years_exp / 8.0) * (0.95 if has_em_skills else 0.2)

        # Cast everything safely to floats
        return {
            "learning_velocity": {
                "continuous_learning_score": float(round(learning_score, 2)),
                "technology_adoption_speed": adoption_speed,
                "upskilling_rate": float(round(learning_score * 0.9, 2)),
                "certification_frequency": float(round(cert_count / max(1.0, years_exp), 2))
            },
            "potentials": {
                "growth_potential": float(growth_potential),
                "innovation_potential": float(round(innovation_potential, 2)),
                "adaptability": float(round(adaptability, 2)),
                "problem_solving": float(round(problem_solving, 2)),
                "leadership_potential": float(round(leadership_potential, 2)),
                "future_learning_capacity": float(round(learning_score, 2))
            },
            "role_readiness": {
                "junior_level": float(round(junior_readiness, 2)),
                "mid_level": float(round(mid_readiness, 2)),
                "senior_level": float(round(senior_readiness, 2)),
                "lead_level": float(round(lead_readiness, 2)),
                "architect_level": float(round(architect_readiness, 2)),
                "engineering_manager_level": float(round(em_readiness, 2))
            }
        }

potential_engine = CandidatePotentialEngine()
