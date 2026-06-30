import re
from typing import Any, Dict, List
from app.schemas.candidate import CandidateProfile
from app.services.candidate_analyzers.project_analyzer import project_analyzer

class ProjectEvidenceAnalyzer:
    """
    Evaluates individual projects to assign an evidence validation score based on
    production-readiness indicators, architectural complexity, deployment depth, and testing.
    """

    PRODUCTION_READY_KWS = ["production", "live", "deployed to production", "prod", "monitoring", "prometheus", "grafana", "sentry", "alerting"]
    ARCH_KWS = ["microservices", "serverless", "event-driven", "monolithic", "distributed", "cqrs", "event sourcing"]
    TEST_KWS = ["pytest", "jest", "unit test", "integration test", "cypress", "selenium", "tdd", "bdd", "ci/cd", "pipeline"]

    def analyze_projects(self, profile: CandidateProfile) -> Dict[str, Any]:
        # Reuse Prompt 5 project analyzer for baseline metrics
        baseline = project_analyzer.analyze(profile)
        projects_evidence = []
        overall_evidence_score = 0.0

        for idx, p in enumerate(baseline["projects"]):
            p_profile = profile.projects[idx]
            desc = p_profile.description or ""
            resps = " ".join(p_profile.responsibilities)
            corpus = f"{p_profile.name} {desc} {' '.join(p_profile.technologies)} {resps}".lower()

            # Production readiness
            prod_ready_hits = [kw for kw in self.PRODUCTION_READY_KWS if kw in corpus]
            prod_ready = len(prod_ready_hits) > 0

            # Architecture pattern
            arch_hits = [kw for kw in self.ARCH_KWS if kw in corpus]
            architecture = arch_hits[0].title() if arch_hits else "Standard / Monolithic"

            # Testing indicators
            test_hits = [kw for kw in self.TEST_KWS if kw in corpus]
            testing = len(test_hits) > 0

            # Compute Project Evidence Score (rating out of 100)
            base_score = p["project_score"]
            boost = 0.0
            if prod_ready:
                boost += 8.0
            if testing:
                boost += 7.0
            
            project_evidence_score = min(100.0, base_score + boost)

            projects_evidence.append({
                "project_name": p["project_name"],
                "domain": p["domain"],
                "complexity": p["complexity"],
                "scale": p["scale"],
                "ownership": p["ownership"],
                "architecture": architecture,
                "production_ready": bool(prod_ready),
                "testing_implemented": bool(testing),
                "deployment_exposure": p["deployment_experience"],
                "cloud_usage": p["cloud_usage"],
                "security_awareness": p["security_awareness"],
                "project_score": float(p["project_score"]),
                "project_evidence_score": float(round(project_evidence_score, 1)),
                "evidence_sources": p["evidence"]
            })

        if projects_evidence:
            overall_evidence_score = sum(pe["project_evidence_score"] for pe in projects_evidence) / len(projects_evidence)

        return {
            "projects": projects_evidence,
            "average_project_evidence_score": float(round(overall_evidence_score, 1))
        }

project_evidence_analyzer = ProjectEvidenceAnalyzer()
