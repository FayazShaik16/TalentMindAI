import re
from datetime import date
from typing import Any, Dict, List
from app.schemas.candidate import CandidateProfile, ExperienceDetail, ProjectDetail
from app.services.extractor import parse_date

class SkillEvidenceEngine:
    """
    Evaluates claimed candidate skills against project history, experiences, and certifications.
    Assigns Verified, Likely, Weak, or Unsupported status based on usage timeline and context evidence.
    """

    def _get_exp_duration_months(self, exp: ExperienceDetail) -> int:
        s_date = parse_date(exp.start_date)
        e_date = parse_date(exp.end_date) or date.today()
        if not s_date:
            return 12  # fallback
        delta = (e_date.year - s_date.year) * 12 + (e_date.month - s_date.month)
        return max(3, delta)

    def verify_skills(self, profile: CandidateProfile) -> Dict[str, Any]:
        results = {}
        
        # Candidate claimed skills from profile
        claimed_skills = {s.normalized_name or s.name for s in profile.skills}
        # Also grab any skill mentioned in projects
        for p in profile.projects:
            for t in p.technologies:
                claimed_skills.add(t.strip())

        for skill in claimed_skills:
            skill_clean = skill.strip()
            if not skill_clean:
                continue

            skill_pat = r"\b" + re.escape(skill_clean.lower()) + r"\b"
            
            evidence_sources = []
            contradictions = []
            duration_months = 0
            project_count = 0
            experience_count = 0
            recent_usage = False
            cert_matching = False

            # 1. Search across certifications
            for cert in profile.certifications:
                if re.search(skill_pat, cert.name.lower()):
                    cert_matching = True
                    evidence_sources.append(f"Certification: {cert.name}")

            # 2. Search across projects
            for p in profile.projects:
                p_text = f"{p.name} {p.description or ''} {' '.join(p.technologies)} {' '.join(p.responsibilities)}".lower()
                if re.search(skill_pat, p_text) or any(skill_clean.lower() == t.strip().lower() for t in p.technologies):
                    project_count += 1
                    dur = p.duration_months or 6
                    duration_months += dur
                    evidence_sources.append(f"Project '{p.name}' (Tech/Responsibilities)")

            # 3. Search across experiences
            for idx, exp in enumerate(profile.experiences):
                exp_text = f"{exp.company_name} {exp.job_title} {exp.description or ''}".lower()
                if re.search(skill_pat, exp_text):
                    experience_count += 1
                    dur = self._get_exp_duration_months(exp)
                    duration_months += dur
                    evidence_sources.append(f"Experience at {exp.company_name} ({exp.job_title})")
                    
                    if exp.is_current or idx == len(profile.experiences) - 1:
                        recent_usage = True

            # If years of experience is extremely high but no matching description detail, flag contradiction
            years_used = round(duration_months / 12.0, 1)
            
            # Technology combinations check (e.g. claims Kubernetes but never worked with Docker or cloud platforms)
            # We can check and apply a penalty or add contradiction if they claim advanced cloud without platforms
            if skill_clean.lower() in ["kubernetes", "docker", "terraform"] and not any(
                p_plat in [s.lower() for s in claimed_skills] for p_plat in ["aws", "gcp", "azure", "cloud"]
            ):
                contradictions.append(f"Claims DevOps skill '{skill_clean}' but has zero cloud platform exposure.")

            # Classification rules
            risk_penalty = 0.0
            if contradictions:
                risk_penalty = 15.0

            if years_used >= 3.0 and project_count >= 2 and experience_count >= 1 and recent_usage:
                status = "Verified"
                base_score = 92.0
                confidence = 0.95
            elif years_used >= 1.0 or (project_count >= 1 and recent_usage) or cert_matching:
                status = "Likely"
                base_score = 75.0
                confidence = 0.82
            elif years_used > 0.0 or project_count >= 1:
                status = "Weak"
                base_score = 45.0
                confidence = 0.65
            else:
                status = "Unsupported"
                base_score = 15.0
                confidence = 0.30

            evidence_score = max(0.0, base_score - risk_penalty)
            
            results[skill_clean] = {
                "skill": skill_clean,
                "status": status,
                "duration_years": float(years_used),
                "project_count": int(project_count),
                "experience_count": int(experience_count),
                "recent_usage": bool(recent_usage),
                "evidence_sources": evidence_sources,
                "contradictions": contradictions,
                "risk_penalty": float(risk_penalty),
                "evidence_score": float(evidence_score),
                "confidence_score": float(confidence)
            }

        return results

skill_evidence_engine = SkillEvidenceEngine()
