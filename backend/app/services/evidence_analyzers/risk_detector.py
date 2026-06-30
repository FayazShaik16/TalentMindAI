import re
from datetime import date
from typing import Any, Dict, List
from app.schemas.candidate import CandidateProfile
from app.services.extractor import parse_date

class RiskDetectionEngine:
    """
    Scans candidate profile, timelines, and verified skills to detect risks (keyword stuffing,
    tech inflation, job hopping, gaps, contradictions, unsupported leadership claims) and outputs risk levels.
    """

    def _get_year(self, date_val, default: int) -> int:
        d = parse_date(date_val)
        return d.year if d else default

    def detect_risks(self, profile: CandidateProfile, skills_verification: Dict[str, Any]) -> Dict[str, Any]:
        explanations = []
        risk_score = 0
        current_year = date.today().year

        # 1. Keyword Stuffing
        # Check ratio of skills to years experience
        years_exp = max(1.0, float(profile.engineered_features.years_experience))
        skills_count = len(profile.skills)
        skills_ratio = skills_count / years_exp
        if skills_ratio > 4.5 and skills_count > 15:
            risk_score += 25
            explanations.append(
                f"Potential Keyword Stuffing: Candidate claims {skills_count} skills for only {years_exp:.1f} years of experience (Ratio: {skills_ratio:.1f})."
            )

        # 2. Technology Inflation
        # Check if they claim expert levels or high scores for items with minimal years
        inflated_techs = []
        for tech, verification in skills_verification.items():
            if verification["status"] in ["Verified", "Likely"] and verification["duration_years"] < 0.6:
                inflated_techs.append(tech)

        if inflated_techs:
            risk_score += min(30, len(inflated_techs) * 10)
            explanations.append(
                f"Technology Inflation: Claimed usage matches verified/likely profile but actual experience duration in projects/roles is < 6 months for: {', '.join(inflated_techs)}."
            )

        # 3. Frequent Job Hopping
        avg_tenure = float(profile.engineered_features.average_tenure)
        companies_count = int(profile.engineered_features.distinct_companies)
        if avg_tenure > 0 and avg_tenure < 1.2 and companies_count >= 3:
            risk_score += 20
            explanations.append(
                f"Frequent Job Hopping: Average tenure is only {avg_tenure:.1f} years across {companies_count} companies."
            )

        # 4. Large Employment Gaps
        # Check if gaps exist (> 6 months)
        sorted_exps = sorted(
            [e for e in profile.experiences if parse_date(e.start_date) is not None],
            key=lambda x: parse_date(x.start_date) or date.min
        )
        prev_end_date = None
        gap_count = 0
        for exp in sorted_exps:
            s_date = parse_date(exp.start_date)
            if prev_end_date and s_date:
                gap = (s_date.year - prev_end_date.year) * 12 + (s_date.month - prev_end_date.month)
                if gap > 6:
                    gap_count += 1
            prev_end_date = parse_date(exp.end_date) or date.today()

        if gap_count > 0:
            risk_score += min(15, gap_count * 5)
            explanations.append(f"Gaps in Employment: Detected {gap_count} gaps longer than 6 months in career history.")

        # 5. Skill Inconsistency (Unsupported skills)
        unsupported_techs = [tech for tech, verification in skills_verification.items() if verification["status"] == "Unsupported"]
        if len(unsupported_techs) > 3:
            risk_score += 15
            explanations.append(
                f"Skill Inconsistency: Claimed skills lack project/experience validation details for: {', '.join(unsupported_techs[:5])}."
            )

        # 6. Unsupported Leadership Claims
        # Claims lead/manager title but has 0 leadership score or has zero mentoring evidence
        has_lead_title = any(
            any(kw in e.job_title.lower() for kw in ["lead", "manager", "architect", "director"])
            for e in profile.experiences
        )
        leadership_score = int(profile.engineered_features.leadership_score)
        if has_lead_title and leadership_score < 2:
            risk_score += 15
            explanations.append(
                "Unsupported Leadership Claims: Profile titles suggest Lead/Manager exposure, but descriptions show minimal mentoring or team steering evidence."
            )

        # Determine overall Risk Level
        if risk_score >= 50:
            risk_level = "High"
            confidence = 0.90
        elif risk_score >= 20:
            risk_level = "Medium"
            confidence = 0.85
        elif risk_score > 0:
            risk_level = "Low"
            confidence = 0.75
        else:
            risk_level = "None"
            confidence = 0.95

        return {
            "risk_level": risk_level,
            "risk_score": int(risk_score),
            "confidence_score": float(confidence),
            "explanations": explanations
        }

risk_detector = RiskDetectionEngine()
