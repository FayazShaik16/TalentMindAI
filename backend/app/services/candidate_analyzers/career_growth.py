from typing import Any, Dict
from app.schemas.candidate import CandidateProfile

class CareerGrowthAnalyzer:
    """
    Computes normalized metrics (0.0 to 1.0) for growth velocity, promotion rate,
    role expansion, learning rate, technology evolution, adaptability, and stability.
    """

    def analyze(self, profile: CandidateProfile, career_data: Dict[str, Any], tech_data: Dict[str, Any]) -> Dict[str, Any]:
        experiences = profile.experiences
        projects = profile.projects
        skills = profile.skills
        features = profile.engineered_features

        # Total years
        years_exp = float(features.years_experience) if hasattr(features, 'years_experience') else 1.0
        years_exp = max(1.0, years_exp)

        # 1. Promotion Rate
        promotions = career_data.get("career_progression", {}).get("promotions_count", 0)
        promotion_rate = min(1.0, float(promotions / years_exp))

        # 2. Growth Velocity
        # Combines promotion frequency and title height
        title_progression_score = 0.2 # baseline
        has_senior = False
        has_lead_arch = False
        has_manager_vp = False

        for exp in experiences:
            title = exp.job_title.lower()
            if any(kw in title for kw in ["vp", "chief", "director", "head"]):
                has_manager_vp = True
            elif any(kw in title for kw in ["lead", "architect", "principal", "manager"]):
                has_lead_arch = True
            elif "senior" in title:
                has_senior = True

        if has_manager_vp:
            title_progression_score = 1.0
        elif has_lead_arch:
            title_progression_score = 0.8
        elif has_senior:
            title_progression_score = 0.5

        # Speed of progression
        growth_velocity = min(1.0, promotion_rate * 1.5 + title_progression_score * 0.4)

        # 3. Role Expansion
        # Measures if responsibility length or project ownership has increased
        ownership_lead_count = 0
        for p in projects:
            resps = " ".join(p.responsibilities).lower()
            if any(kw in resps for kw in ["spearheaded", "architected", "designed", "led", "managed", "owned"]):
                ownership_lead_count += 1
        
        role_expansion = min(1.0, (len(experiences) * 0.10) + (ownership_lead_count * 0.20))

        # 4. Learning Rate
        # Distinct technologies / years of experience
        tech_count = career_data.get("technical_profile", {}).get("breadth_count", 1)
        learning_rate = min(1.0, float(tech_count / (years_exp * 3.0)))

        # 5. Technology Evolution
        # Measures acquisition of modern high-value tech (cloud, ai, cyber, blockchain etc.)
        cloud = float(features.cloud_score) if hasattr(features, 'cloud_score') else 0.0
        ai = float(features.ai_score) if hasattr(features, 'ai_score') else 0.0
        blockchain = float(features.blockchain_score) if hasattr(features, 'blockchain_score') else 0.0
        cyber = float(features.cybersecurity_score) if hasattr(features, 'cybersecurity_score') else 0.0
        
        tech_evo_score = min(1.0, (cloud + ai + blockchain + cyber) / 10.0)

        # 6. Adaptability
        # Company diversity + Domain diversity
        company_count = len(set([exp.company_name for exp in experiences]))
        domain_count = career_data.get("diversity", {}).get("domain_diversity_count", 0)
        adaptability = min(1.0, (company_count * 0.12) + (domain_count * 0.15))

        # 7. Long-term Stability
        avg_tenure = float(features.average_tenure) if hasattr(features, 'average_tenure') else 0.0
        stability_score = min(1.0, avg_tenure / 5.0) # 5 years = 1.0 stability

        return {
            "growth_velocity": float(round(growth_velocity, 2)),
            "promotion_rate": float(round(promotion_rate, 2)),
            "role_expansion": float(round(role_expansion, 2)),
            "learning_rate": float(round(learning_rate, 2)),
            "technology_evolution": float(round(tech_evo_score, 2)),
            "adaptability": float(round(adaptability, 2)),
            "long_term_stability": float(round(stability_score, 2))
        }

career_growth_analyzer = CareerGrowthAnalyzer()
