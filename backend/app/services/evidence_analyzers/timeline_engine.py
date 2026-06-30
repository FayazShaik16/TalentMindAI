import re
from datetime import date, datetime
from typing import Any, Dict, List, Set
from app.schemas.candidate import CandidateProfile, ExperienceDetail, ProjectDetail
from app.services.extractor import parse_date

class TechnologyTimelineEngine:
    """
    Generates a chronological timeline of technology usage and evaluates career progression metrics.
    """

    KNOWN_TECHS = [
        "python", "javascript", "typescript", "java", "go", "golang", "c++", "rust", "c#", "ruby", "php",
        "react", "angular", "vue", "django", "flask", "fastapi", "spring", "express", "next.js", "nextjs",
        "aws", "gcp", "azure", "docker", "kubernetes", "k8s", "terraform", "ansible", "jenkins",
        "postgresql", "mysql", "mongodb", "redis", "sql", "kafka", "rabbitmq", "grpc", "microservices",
        "pytorch", "tensorflow", "machine learning", "nlp", "llm", "llms", "langchain", "gpt"
    ]

    def _get_year(self, date_val: str | datetime | None, default: int) -> int:
        d = parse_date(date_val)
        return d.year if d else default

    def generate_timeline(self, profile: CandidateProfile) -> Dict[int, List[str]]:
        timeline: Dict[int, Set[str]] = {}
        current_year = date.today().year

        # 1. Map technologies from experiences by active years
        for exp in profile.experiences:
            s_year = self._get_year(exp.start_date, current_year - 1)
            e_year = self._get_year(exp.end_date if not exp.is_current else None, current_year)

            # Find matching technologies in experience text
            exp_text = f"{exp.job_title} {exp.description or ''}".lower()
            matched_techs = set()
            for tech in self.KNOWN_TECHS:
                if re.search(r"\b" + re.escape(tech) + r"\b", exp_text):
                    matched_techs.add(tech.title() if tech not in ["aws", "gcp", "k8s"] else tech.upper())

            # Map to active years
            for year in range(s_year, e_year + 1):
                if year not in timeline:
                    timeline[year] = set()
                timeline[year].update(matched_techs)

        # 2. Map technologies from projects
        # Assume projects are active in the years corresponding to when they were completed (roughly recent years or experience year bounds)
        # To be clean: find the candidate experience company or duration bounds if we can match project dates
        # Since project schema doesn't have start/end dates directly (only duration_months),
        # we assume projects are active in recent years (up to current_year) or correspond to the candidate's active years.
        # Let's map project tech to the current active years of candidate experiences.
        # Alternatively, if there is a way to place them, we place them in the current_year and previous years based on duration.
        for p in profile.projects:
            p_techs = [t.strip() for t in p.technologies if t.strip()]
            # Estimate project year: if candidate is in a current role, default to current_year
            # Let's add them to the recent years spanning the duration
            dur_years = max(1, round((p.duration_months or 6) / 12))
            for offset in range(dur_years):
                year = current_year - offset
                if year not in timeline:
                    timeline[year] = set()
                # Normalize and add
                for t in p_techs:
                    timeline[year].add(t.title() if t.lower() not in ["aws", "gcp", "k8s"] else t.upper())

        # Clean and sort
        sorted_timeline = {}
        for year in sorted(timeline.keys()):
            # Filter out empty years and sort lists
            techs = sorted(list(timeline[year]))
            if techs:
                sorted_timeline[year] = techs

        return sorted_timeline

    def analyze_progression(self, profile: CandidateProfile, timeline: Dict[int, List[str]]) -> Dict[str, Any]:
        experiences = profile.experiences
        current_year = date.today().year
        
        # 1. Career stability & hopping
        avg_tenure = profile.engineered_features.average_tenure
        hopping = bool(avg_tenure > 0 and avg_tenure < 1.5 and len(experiences) >= 3)
        resilience = "High" if avg_tenure >= 3.0 else "Medium" if avg_tenure >= 1.5 else "Low"

        # 2. Technology evolution
        # Check if they transition from basic backend frameworks to cloud/AI/Kubernetes
        years = sorted(timeline.keys())
        evolution_trail = []
        acceleration = "Stable"
        
        if len(years) >= 2:
            first_year_techs = [t.lower() for t in timeline[years[0]]]
            last_year_techs = [t.lower() for t in timeline[years[-1]]]
            
            # Check if advanced tech is introduced
            advanced_techs = ["kubernetes", "k8s", "terraform", "pytorch", "tensorflow", "llm", "langchain", "aws", "gcp"]
            has_advanced_start = any(t in first_year_techs for t in advanced_techs)
            has_advanced_end = any(t in last_year_techs for t in advanced_techs)
            
            if not has_advanced_start and has_advanced_end:
                acceleration = "Accelerated upslowing (Transitioned to Cloud/AI ecosystem)"
            elif has_advanced_end:
                acceleration = "High-tech specialization maintained"
            
            evolution_trail.append(f" upslowing trail from {years[0]} ({len(first_year_techs)} techs) to {years[-1]} ({len(last_year_techs)} techs)")

        # 3. Promotions & transitions
        promotions = 0
        specialization = "Generalist"
        roles = [e.job_title.lower() for e in experiences]
        
        # Count title increments
        for r in roles:
            if any(kw in r for kw in ["senior", "lead", "principal", "manager", "head", "director", "architect"]):
                promotions += 1

        # Check specialization
        backend_hits = sum(1 for r in roles if "backend" in r or "systems" in r)
        frontend_hits = sum(1 for r in roles if "frontend" in r or "ui" in r or "web" in r)
        management_hits = sum(1 for r in roles if "manager" in r or "director" in r or "lead" in r)

        if backend_hits > frontend_hits and backend_hits > management_hits:
            specialization = "Backend Specialization"
        elif frontend_hits > backend_hits and frontend_hits > management_hits:
            specialization = "Frontend Specialization"
        elif management_hits > backend_hits and management_hits > frontend_hits:
            specialization = "Engineering Leadership"
        elif backend_hits > 0 and frontend_hits > 0:
            specialization = "Full Stack Generalist"

        stagnation = False
        # If candidate has been in the same company for > 5 years without title updates
        for exp in experiences:
            # Estimate years in company
            s_year = self._get_year(exp.start_date, current_year)
            e_year = self._get_year(exp.end_date if not exp.is_current else None, current_year)
            if (e_year - s_year) >= 5 and promotions == 0:
                stagnation = True

        return {
            "career_consistency": "Consistent" if not hopping else "Job Hopper Tendencies",
            "promotion_history_count": int(promotions),
            "role_specialization": specialization,
            "career_resilience": resilience,
            "technology_evolution_acceleration": acceleration,
            "stagnation_detected": bool(stagnation),
            "timeline_analysis": "".join(evolution_trail)
        }

timeline_engine = TechnologyTimelineEngine()
