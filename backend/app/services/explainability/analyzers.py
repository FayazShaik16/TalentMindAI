from typing import Any, Dict, List
from app.schemas.candidate import CandidateProfile
from app.database.models.candidate_intelligence import CandidateIntelligence
from app.database.models.candidate_evidence import CandidateEvidence

class StrengthAnalyzer:
    def analyze(
        self,
        candidate_profile: CandidateProfile,
        intelligence: CandidateIntelligence | None,
        evidence: CandidateEvidence | None,
        ranking_item: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Extracts candidate strengths across Technical, Leadership, Career, Domain, and Learning vectors.
        Ranks them by impact.
        """
        strengths = []

        # 1. Technical Strengths
        expert_skills = []
        if intelligence:
            tech_details = intelligence.technical_intelligence.get("all_tech_details", {})
            for skill, details in tech_details.items():
                if details.get("proficiency_level") in ["Expert", "Advanced"]:
                    expert_skills.append(f"{skill} ({details.get('proficiency_level')})")
        
        if expert_skills:
            strengths.append({
                "name": "Advanced Technical Proficiency",
                "category": "Technical",
                "evidence": f"Demonstrated deep expertise in: {', '.join(expert_skills[:3])}.",
                "impact": "High"
            })

        # 2. Leadership Strengths
        if intelligence:
            lead_score = intelligence.leadership_intelligence.get("overall_leadership_score", 0.0)
            if lead_score >= 70.0:
                readiness = intelligence.leadership_intelligence.get("team_leadership", {}).get("level", "Contributor")
                strengths.append({
                    "name": "Proven Engineering Leadership",
                    "category": "Leadership",
                    "evidence": f"Scored {lead_score:.1f}/100 in leadership intelligence. Readiness level classified as: {readiness}.",
                    "impact": "High"
                })

        # 3. Career Strengths
        if intelligence:
            stability = intelligence.career_intelligence.get("career_stability", {}).get("stability_score", 0.0)
            if stability >= 75.0:
                strengths.append({
                    "name": "Strong Career Stability",
                    "category": "Career",
                    "evidence": f"Average tenure matches stability standards (Score: {stability:.1f}/100). Low employment churn risk.",
                    "impact": "Medium"
                })

        # 4. Domain Strengths
        if intelligence:
            domains = list(intelligence.domain_intelligence.get("detected_domains", {}).keys())
            if domains:
                strengths.append({
                    "name": "Diverse Industry Exposure",
                    "category": "Domain",
                    "evidence": f"Possesses verified experience in domains: {', '.join(domains[:3])}.",
                    "impact": "Medium"
                })

        # 5. Learning/Potential Strengths
        if evidence and "potential_metrics" in evidence.potential_metrics:
            learning_velocity = evidence.potential_metrics.get("learning_velocity", {}).get("technology_adoption_speed", "Medium")
            if learning_velocity in ["High", "Medium"]:
                strengths.append({
                    "name": "High Upskilling Velocity",
                    "category": "Learning",
                    "evidence": f"Classified with '{learning_velocity}' technology adoption speed and continuous learning rating.",
                    "impact": "High" if learning_velocity == "High" else "Medium"
                })

        # Sort strengths by impact (High first, then Medium, then Low)
        impact_weights = {"High": 3, "Medium": 2, "Low": 1}
        sorted_strengths = sorted(strengths, key=lambda x: impact_weights.get(x["impact"], 0), reverse=True)

        if not sorted_strengths:
            # Fallback strength if none are detected
            exp_years = candidate_profile.engineered_features.years_experience if candidate_profile.engineered_features else 0.0
            if exp_years >= 3.0:
                sorted_strengths.append({
                    "name": "Mid-to-Senior Professional Experience",
                    "category": "Career",
                    "evidence": f"Possesses {exp_years:.1f} years of verified professional experience in the industry.",
                    "impact": "Medium"
                })
            else:
                sorted_strengths.append({
                    "name": "Baseline Skill Alignment",
                    "category": "Technical",
                    "evidence": "Demonstrated matching capabilities for core role requirements.",
                    "impact": "Medium"
                })
        return sorted_strengths


class WeaknessAnalyzer:
    def analyze(
        self,
        candidate_profile: CandidateProfile,
        intelligence: CandidateIntelligence | None,
        evidence: CandidateEvidence | None,
        ranking_item: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Identifies gaps in technical skills, experience metrics, or leadership criteria, mapping severity.
        """
        weaknesses = []

        # 1. Missing Technical Gaps
        missing_skills = ranking_item.get("missing_skills", [])
        if missing_skills:
            weaknesses.append({
                "name": "Technical Stack Gaps",
                "category": "Technical",
                "evidence": f"Lacks direct matching evidence for required skills: {', '.join(missing_skills[:3])}.",
                "severity": "High" if len(missing_skills) > 2 else "Medium"
            })

        # 2. Experience Gaps
        total_years = candidate_profile.engineered_features.years_experience
        if total_years < 3.0:
            weaknesses.append({
                "name": "Limited Total Experience",
                "category": "Experience",
                "evidence": f"Candidate possesses {total_years:.1f} years of total experience, which is below mid-to-senior levels.",
                "severity": "High"
            })

        # 3. Leadership Gaps
        if intelligence:
            lead_score = intelligence.leadership_intelligence.get("overall_leadership_score", 0.0)
            if lead_score < 45.0:
                weaknesses.append({
                    "name": "Limited Mentoring/Leadership Exposure",
                    "category": "Leadership",
                    "evidence": f"Scored {lead_score:.1f}/100 in leadership indicators. responsibilities lack team lead or mentor evidence.",
                    "severity": "Medium"
                })

        # 4. Risk Detection Warnings
        if evidence and "risk_analysis" in evidence.risk_analysis:
            risk_data = evidence.risk_analysis
            risk_score = risk_data.get("risk_score", 0)
            if risk_score > 15:
                weaknesses.append({
                    "name": "Resume Consistency Warnings",
                    "category": "Risk",
                    "evidence": f"Risk detector flagged resume flags: {', '.join(risk_data.get('explanations', []))}.",
                    "severity": "Critical" if risk_score > 35 else "High"
                })

        # Sort weaknesses by severity (Critical first, then High, then Medium, then Low)
        severity_weights = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
        return sorted(weaknesses, key=lambda x: severity_weights.get(x["severity"], 0), reverse=True)


class TransferableSkillsFinder:
    # Common transferable skills mapping
    TRANSFER_MAP = {
        "fastapi": ("flask", "Flask provides similar REST API routing structure, candidate can easily adapt to FastAPI asynchronous decorators."),
        "kubernetes": ("docker swarm", "Docker Swarm experience establishes core container orchestration concepts transferable to Kubernetes pods/services."),
        "pytorch": ("tensorflow", "TensorFlow workflows are highly equivalent to PyTorch graphs. Core neural networks understanding is transferable."),
        "postgresql": ("mysql", "MySQL experience establishes relational DB optimization, SQL indexes, and schemas transferable to PostgreSQL."),
        "next.js": ("react", "React underpins Next.js. Candidate understands component lifecycles and virtual DOM concepts."),
        "typescript": ("javascript", "Javascript establishes core syntax. Candidate needs low effort to adopt static typing interfaces in TypeScript.")
    }

    def find(self, missing_skills: List[str], candidate_skills: List[str]) -> List[Dict[str, str]]:
        """
        Maps missing job requirements to candidate's alternative transferable capabilities.
        """
        transferable = []
        cand_set = set([s.lower() for s in candidate_skills])

        for ms in missing_skills:
            ms_clean = ms.lower()
            if ms_clean in self.TRANSFER_MAP:
                source_skill, explanation = self.TRANSFER_MAP[ms_clean]
                if source_skill in cand_set:
                    transferable.append({
                        "missing_skill": ms,
                        "transferable_skill": source_skill.title(),
                        "explanation": explanation
                    })
        return transferable


class MissingSkillsEngine:
    def analyze(self, missing_skills: List[str], transferable: List[Dict[str, str]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Categorizes missing skills and estimates learning effort.
        """
        critical = []
        important = []
        nice_to_have = []
        
        transfer_missing = set([t["missing_skill"].lower() for t in transferable])

        for i, ms in enumerate(missing_skills):
            ms_clean = ms.lower()
            
            # Simple heuristic: first few missing skills are critical, transferable are important, others nice-to-have
            if ms_clean in transfer_missing:
                important.append({
                    "name": ms,
                    "learning_effort": "Low (1-2 weeks)",
                    "actionable_suggestion": f"Leverage transferable skill to pick up {ms} principles."
                })
            elif i < 2:
                critical.append({
                    "name": ms,
                    "learning_effort": "High (2-3 months)",
                    "actionable_suggestion": f"Focus interview on assessing baseline knowledge of {ms} ecosystems."
                })
            else:
                nice_to_have.append({
                    "name": ms,
                    "learning_effort": "Medium (3-4 weeks)",
                    "actionable_suggestion": f"Upskill in {ms} using online courses or internal labs."
                })

        return {
            "critical_missing": critical,
            "important_missing": important,
            "nice_to_have_missing": nice_to_have
        }


class InterviewRecommendationEngine:
    def generate(
        self,
        ranking_item: Dict[str, Any],
        strengths: List[Dict[str, Any]],
        weaknesses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generates customized interview plan guidelines and focus topics.
        """
        rec = ranking_item.get("recommendation", "Interview")
        
        focus_areas = []
        # 1. Technical Focus Area if there are weaknesses
        tech_weaks = [w for w in weaknesses if w["category"] == "Technical"]
        if tech_weaks:
            focus_areas.append({
                "topic": "Technical Stack Alignment & Gaps",
                "questions": [
                    f"Explain how you would bridge the lack of direct production exposure to: {', '.join(ranking_item.get('missing_skills', [])[:2])}.",
                    "Provide examples of transferring your alternative frameworks knowledge to pick up missing tech on a short schedule."
                ]
            })
        else:
            focus_areas.append({
                "topic": "Technical Deep Dive",
                "questions": [
                    "Walk us through the architecture design of your most complex project.",
                    "Describe your experience with scaling database transactions under high parallel load."
                ]
            })

        # 2. Leadership Focus Area
        lead_score = ranking_item["scoring_dimensions"]["leadership"]["raw_score"]
        if lead_score >= 70.0:
            focus_areas.append({
                "topic": "Engineering Leadership & Mentoring",
                "questions": [
                    "Describe a scenario where you led a team through major architectural changes or tech migrations.",
                    "How do you approach mentoring junior engineers and resolving technical conflicts?"
                ]
            })
        else:
            focus_areas.append({
                "topic": "Ownership & Collaboration",
                "questions": [
                    "How do you coordinate with cross-functional product teams to deliver complex requirements?",
                    "Give an example of taking high ownership of a project from design to final cloud deployment."
                ]
            })

        # 3. Risk & Career Stability Focus Area
        risk_score = ranking_item["scoring_dimensions"].get("risk", {}).get("raw_score", 100.0)
        if risk_score < 80.0:
            focus_areas.append({
                "topic": "Career Consistency & Delivery Audit",
                "questions": [
                    "Explain the anomalies flagged in your role progression timeline.",
                    "Describe your work transitions and how you maintain execution consistency."
                ]
            })
        else:
            focus_areas.append({
                "topic": "Continuous Learning Trajectory",
                "questions": [
                    "How do you determine which new technologies to adopt in your current engineering pipelines?",
                    "Describe a technology you adopted recently and how you applied it in production."
                ]
            })

        return {
            "overall_recommendation": rec,
            "interview_focus_areas": focus_areas
        }


class HiringNarrativeGenerator:
    def generate(
        self,
        candidate_profile: CandidateProfile,
        ranking_item: Dict[str, Any],
        strengths: List[Dict[str, Any]],
        weaknesses: List[Dict[str, Any]]
    ) -> str:
        """
        Generates recruiter-friendly factual summary narrative paragraphs based on candidate data.
        """
        first_name = candidate_profile.personal_info.first_name or ""
        last_name = candidate_profile.personal_info.last_name or ""
        name = f"{first_name} {last_name}".strip() or "The candidate"
        
        years = candidate_profile.engineered_features.years_experience
        rec = ranking_item.get("recommendation", "Interview")
        score = ranking_item.get("overall_score", 50.0)
        conf = ranking_item.get("hiring_confidence", 0.7)

        # 1. Experience summary
        exp_parts = []
        experiences = candidate_profile.experiences or []
        current_exp = next((e for e in experiences if e.is_current), None)
        if not current_exp and experiences:
            current_exp = experiences[0]

        if current_exp:
            role = current_exp.job_title or "Engineer"
            comp = current_exp.company_name or "their current employer"
            exp_parts.append(f"currently works as {role} at {comp}")
        
        other_exps = [e for e in experiences if e != current_exp]
        if other_exps:
            notable_companies = list(dict.fromkeys([e.company_name for e in other_exps if e.company_name]))
            if notable_companies:
                exp_parts.append(f"with prior experience at {', '.join(notable_companies[:3])}")
        
        exp_desc = " ".join(exp_parts)
        if exp_desc:
            exp_desc = f"They {exp_desc}."

        # 2. Project summary
        proj_parts = []
        projects = candidate_profile.projects or []
        if projects:
            proj_desc_items = []
            for p in projects[:2]:
                p_name = p.name or "Key Project"
                p_techs = p.technologies or []
                p_dom = p.domain or ""
                p_desc = f"'{p_name}'"
                if p_techs:
                    p_desc += f" (built with {', '.join(p_techs[:3])})"
                if p_dom:
                    p_desc += f" in the {p_dom} domain"
                proj_desc_items.append(p_desc)
            if proj_desc_items:
                proj_parts.append(f"Key projects in their portfolio include: {', and '.join(proj_desc_items)}")
        
        proj_desc = ". ".join(proj_parts)
        if proj_desc:
            proj_desc = f"{proj_desc}."

        # 3. Skills summary
        skills = candidate_profile.skills or []
        skill_names = [s.name for s in skills if s.name]
        skill_desc = ""
        if skill_names:
            skill_desc = f"Their technical skill set is anchored by core capabilities in: {', '.join(skill_names[:6])}."

        # 4. Education & Certifications
        edu_cert_parts = []
        educations = candidate_profile.educations or []
        if educations:
            edu = educations[0]
            deg = edu.degree or "Degree"
            field = edu.field_of_study or ""
            inst = edu.institution or ""
            edu_str = f"holds a {deg}"
            if field:
                edu_str += f" in {field}"
            if inst:
                edu_str += f" from {inst}"
            edu_cert_parts.append(edu_str)
            
        certs = candidate_profile.certifications or []
        cert_names = [c.name for c in certs if c.name]
        if cert_names:
            edu_cert_parts.append(f"holds certifications including {', '.join(cert_names[:3])}")
            
        edu_cert_desc = ""
        if edu_cert_parts:
            edu_cert_desc = f"Qualifications-wise, {name} {' and '.join(edu_cert_parts)}."

        # 5. Fit & Recommendation Summary
        primary_strengths = [s["name"] for s in strengths[:2]]
        primary_weaks = [w["name"] for w in weaknesses[:2]]

        strength_str = ""
        if primary_strengths:
            strength_str = f"Main technical and professional strengths include {', '.join(primary_strengths)}."

        gap_str = ""
        if primary_weaks:
            gap_str = f"Recruiters should audit specific gaps regarding {', '.join(primary_weaks)} during interviews."
        else:
            gap_str = "They exhibit solid alignment with minimal gaps relative to the job requirements."

        # Combine into a cohesive, non-generic narrative paragraph
        narrative_paragraphs = [
            f"Candidate {name} has {years:.1f} years of verified professional experience, yielding an overall match score of {score:.1f}/100 and calibrated hiring confidence of {conf*100:.0f}%, resulting in a '{rec}' recommendation.",
            exp_desc,
            skill_desc,
            proj_desc,
            edu_cert_desc,
            strength_str,
            gap_str
        ]
        
        # Filter empty strings and join
        narrative = " ".join([p for p in narrative_paragraphs if p])
        return narrative
