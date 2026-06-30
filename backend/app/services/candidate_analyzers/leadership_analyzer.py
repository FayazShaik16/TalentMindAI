import re
from typing import Any, Dict, List
from app.schemas.candidate import CandidateProfile

class LeadershipAnalyzer:
    """
    Infers leadership qualities (team management, mentoring, system ownership, cross-team collab, decision making)
    backed by textual evidence from experiences and projects.
    """

    PATTERNS = {
        "team_leadership": [
            r"led\s+a?\s*team", r"managed\s+a?\s*team", r"supervise", r"engineering\s+manager",
            r"team\s+lead", r"lead\s+developer", r"lead\s+engineer", r"head\s+of", r"vp\s+of"
        ],
        "mentoring": [
            r"mentor", r"coach", r"guide\s+junior", r"onboard", r"training", r"advising", r"help\s+junior"
        ],
        "architecture_ownership": [
            r"architected", r"designed\s+system", r"system\s+design", r"technical\s+architecture",
            r"microservices\s+architecture", r"infrastructure\s+design", r"database\s+design"
        ],
        "decision_making": [
            r"made\s+technical\s+decisions", r"evaluated\s+technologies", r"selected\s+tech",
            r"technical\s+roadmap", r"architectural\s+decision", r"defined\s+technical"
        ],
        "cross_functional_collaboration": [
            r"cross-functional", r"collaborated\s+with\s+product", r"product\s+manager",
            r"stakeholder", r"cross\s+team", r"coordinated\s+with", r"business\s+partner"
        ],
        "product_ownership": [
            r"owned\s+product", r"product\s+roadmap", r"product\s+strategy", r"defined\s+requirements",
            r"product\s+owner", r"product\s+backlog", r"feature\s+ownership"
        ],
        "technical_leadership": [
            r"tech\s+lead", r"technical\s+lead", r"technical\s+leadership", r"spearheaded\s+development",
            r"drove\s+code", r"code\s+quality", r"scrum\s+master", r"best\s+practices"
        ]
    }

    def analyze(self, profile: CandidateProfile) -> Dict[str, Any]:
        results = {}
        overall_evidence_count = 0

        # Build corpus by dividing into sentence chunks
        text_corpus = []
        for exp in profile.experiences:
            text_corpus.append(f"{exp.job_title} at {exp.company_name}")
            if exp.description:
                # split into sentences
                sentences = re.split(r'[.!?]\s+', exp.description)
                text_corpus.extend(sentences)

        for p in profile.projects:
            text_corpus.append(f"Project: {p.name}")
            if p.description:
                sentences = re.split(r'[.!?]\s+', p.description)
                text_corpus.extend(sentences)
            for resp in p.responsibilities:
                text_corpus.append(resp)

        for dimension, patterns in self.PATTERNS.items():
            evidence = []
            for sentence in text_corpus:
                clean_sentence = sentence.strip()
                if not clean_sentence:
                    continue
                for pattern in patterns:
                    if re.search(pattern, clean_sentence.lower()):
                        evidence.append(clean_sentence)
                        break # no need to check other patterns for this sentence

            # Remove duplicate evidence sentences
            evidence = list(set(evidence))
            evidence_count = len(evidence)
            overall_evidence_count += evidence_count

            # Determine confidence and presence
            if evidence_count >= 3:
                level = "High"
                score = 0.95
                confidence = 0.93
            elif evidence_count >= 1:
                level = "Medium"
                score = 0.75
                confidence = 0.80
            else:
                level = "None / Inferred low"
                score = 0.20
                confidence = 0.50

            results[dimension] = {
                "level": level,
                "has_exposure": evidence_count > 0,
                "evidence_count": int(evidence_count),
                "evidence": evidence,
                "score": float(score),
                "confidence_score": float(confidence)
            }

        # Calculate overall leadership capacity score
        active_dimensions = sum(1 for d in self.PATTERNS.keys() if results[d]["has_exposure"])
        overall_score = (active_dimensions / len(self.PATTERNS)) * 100.0

        results["overall_leadership_score"] = float(round(overall_score, 1))
        results["overall_confidence_score"] = float(0.90 if active_dimensions > 3 else 0.70 if active_dimensions > 0 else 0.50)

        return results

leadership_analyzer = LeadershipAnalyzer()
