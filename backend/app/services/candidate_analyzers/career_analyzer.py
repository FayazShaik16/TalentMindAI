import re
from typing import Any, Dict, List
from app.schemas.candidate import CandidateProfile

class CareerAnalyzer:
    """
    Analyzes candidate's professional trajectory, progression velocity, promotion rate,
    stability, remote/international exposure, startup vs enterprise presence, and consulting/product dynamics.
    """

    CONSULTING_COMPANIES = {
        "accenture", "tcs", "tata consultancy services", "infosys", "wipro",
        "cognizant", "capgemini", "deloitte", "ey", "pwc", "kpmg", "hcl",
        "tech mahindra", "l&t", "epam", "ust global", "mindtree", "thoughtworks"
    }

    ENTERPRISE_COMPANIES = {
        "microsoft", "google", "amazon", "apple", "meta", "facebook", "netflix",
        "oracle", "sap", "ibm", "salesforce", "cisco", "intel", "hp", "adobe",
        "walmart", "jpmorgan", "goldman sachs", "morgan stanley", "citigroup"
    }

    STARTUP_KEYWORDS = ["startup", "early-stage", "seed", "series a", "series b", "founder", "co-founder", "founding"]
    REMOTE_KEYWORDS = ["remote", "work from home", "wfh", "distributed team", "telecommute"]
    INT_KEYWORDS = ["global", "international", "us", "uk", "europe", "cross-border", "offshore", "overseas", "emea", "apac"]

    def analyze(self, profile: CandidateProfile) -> Dict[str, Any]:
        experiences = profile.experiences
        projects = profile.projects
        skills = profile.skills
        engineered = profile.engineered_features

        # Calculate totals
        total_years = float(engineered.years_experience) if hasattr(engineered, 'years_experience') else 0.0
        unique_companies = list(set([exp.company_name for exp in experiences]))
        company_count = len(unique_companies)

        # 1. Progression & Promotion Frequency
        # Detect promotions (title updates within the same company or upward transitions like Junior -> Senior -> Lead)
        promotions = 0
        role_evolution = []
        
        # Sort experiences by start_date/chronologically if possible, otherwise keep order
        # For simplicity, we parse experiences list
        for exp in experiences:
            role_evolution.append(f"{exp.job_title} at {exp.company_name}")
            title_lower = exp.job_title.lower()
            if any(kw in title_lower for kw in ["senior", "lead", "principal", "manager", "head", "director", "architect"]):
                promotions += 1

        # Promotion frequency (average years to a promotion/upward step)
        prom_frequency_years = round(total_years / max(promotions, 1), 2)

        # 2. Company / Industry Diversity
        company_diversity = "High" if company_count > 4 else ("Medium" if company_count > 2 else "Low")
        
        # Industry domain diversity
        domains = list(set([p.domain for p in projects if p.domain]))
        domain_count = len(domains)
        industry_diversity = "High" if domain_count > 3 else ("Medium" if domain_count > 1 else "Low")

        # 3. Startup vs Enterprise Exposure
        has_startup = False
        has_enterprise = False
        has_consulting = False

        for exp in experiences:
            company_lower = exp.company_name.lower()
            desc_lower = (exp.description or "").lower()

            if any(c in company_lower for c in self.CONSULTING_COMPANIES):
                has_consulting = True
            if any(e in company_lower for e in self.ENTERPRISE_COMPANIES):
                has_enterprise = True
            if any(kw in desc_lower or kw in company_lower for kw in self.STARTUP_KEYWORDS):
                has_startup = True

        # Classify primary focus
        company_type = "Product"
        if has_consulting and not has_enterprise:
            company_type = "Consulting"
        elif has_consulting and has_enterprise:
            company_type = "Hybrid (Product & Consulting)"

        firm_size = "Mid-Market"
        if has_enterprise and has_startup:
            firm_size = "Hybrid (Startup & Enterprise)"
        elif has_enterprise:
            firm_size = "Enterprise"
        elif has_startup:
            firm_size = "Startup"

        # 4. Remote & International Exposure
        remote_experience = False
        remote_count = 0
        international_exposure = False
        international_details = []

        for exp in experiences:
            desc_lower = (exp.description or "").lower()
            if any(kw in desc_lower for kw in self.REMOTE_KEYWORDS):
                remote_experience = True
                remote_count += 1
            if any(kw in desc_lower for kw in self.INT_KEYWORDS):
                international_exposure = True
                matched_kws = [kw for kw in self.INT_KEYWORDS if kw in desc_lower]
                international_details.append(f"Role at {exp.company_name} involved global collaboration (keywords: {', '.join(matched_kws)})")

        for p in projects:
            desc_lower = (p.description or "").lower()
            if any(kw in desc_lower for kw in self.REMOTE_KEYWORDS):
                remote_experience = True
            if any(kw in desc_lower for kw in self.INT_KEYWORDS):
                international_exposure = True
                matched_kws = [kw for kw in self.INT_KEYWORDS if kw in desc_lower]
                international_details.append(f"Project '{p.name}' involved global scope (keywords: {', '.join(matched_kws)})")

        # 5. Tech Breadth and Depth
        all_techs = set()
        for p in projects:
            for t in p.technologies:
                all_techs.add(t.strip().lower())
        for s in skills:
            all_techs.add(s.name.strip().lower())
            if s.normalized_name:
                all_techs.add(s.normalized_name.strip().lower())

        tech_breadth = len(all_techs)
        
        # Estimate depth by finding the longest span or largest keyword association
        # For simplicity, count the maximum mentions/years of a single tech
        tech_depth_score = 0
        if experiences:
            # Maximum projects of a single tech
            tech_counts = {}
            for p in projects:
                for t in p.technologies:
                    t_clean = t.strip().lower()
                    tech_counts[t_clean] = tech_counts.get(t_clean, 0) + 1
            tech_depth_score = max(tech_counts.values()) if tech_counts else 1

        # 6. Growth Trajectory Classification
        if total_years > 0:
            growth_velocity = float(promotions / total_years)
        else:
            growth_velocity = 0.0

        if growth_velocity > 0.4:
            trajectory = "Accelerated Growth"
        elif growth_velocity > 0.2:
            trajectory = "Steady Advancement"
        else:
            trajectory = "Stable / Consolidation"

        return {
            "career_progression": {
                "total_years_experience": float(total_years),
                "promotions_count": int(promotions),
                "promotion_frequency_years": float(prom_frequency_years),
                "role_evolution": role_evolution
            },
            "career_stability": {
                "average_tenure_years": float(engineered.average_tenure) if hasattr(engineered, 'average_tenure') else 0.0,
                "stability_score": float(engineered.career_stability) if hasattr(engineered, 'career_stability') else 0.0,
                "distinct_companies_count": int(company_count)
            },
            "diversity": {
                "company_diversity": company_diversity,
                "industry_diversity": industry_diversity,
                "domain_diversity_count": int(domain_count),
                "domains": domains
            },
            "work_environment": {
                "consulting_vs_product": company_type,
                "startup_vs_enterprise": firm_size,
                "has_startup_exposure": bool(has_startup),
                "has_enterprise_exposure": bool(has_enterprise),
                "has_consulting_exposure": bool(has_consulting)
            },
            "geographic_exposure": {
                "remote_experience": bool(remote_experience),
                "remote_roles_count": int(remote_count),
                "international_exposure": bool(international_exposure),
                "international_details": list(set(international_details))
            },
            "technical_profile": {
                "breadth_count": int(tech_breadth),
                "estimated_depth_score": int(tech_depth_score)
            },
            "growth_trajectory": {
                "velocity_score": float(growth_velocity),
                "trajectory_class": trajectory
            }
        }

career_analyzer = CareerAnalyzer()
