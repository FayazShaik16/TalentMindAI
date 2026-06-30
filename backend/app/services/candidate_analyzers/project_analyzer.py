import re
from typing import Any, Dict, List
from app.schemas.candidate import CandidateProfile, ProjectDetail

class ProjectAnalyzer:
    """
    Evaluates projects for business impact, complexity, scale, tech stack depth,
    ownership level, cloud deployment, and AI components, generating project scores.
    """

    COMPLEXITY_KWS = ["microservices", "optimization", "distributed", "real-time", "latency", "concurrency", "fault-tolerant", "pipeline", "multithreading", "sharding", "asynchronous"]
    SCALE_KWS = ["millions", "throughput", "terabytes", "petabytes", "gigabytes", "scale", "load", "volume", "users", "traffic", "heavy"]
    OWNERSHIP_LEAD_KWS = ["spearheaded", "architected", "designed", "led", "managed", "founded", "solely", "owned"]
    OWNERSHIP_CORE_KWS = ["developed", "implemented", "built", "created", "wrote", "integrated", "engineered"]
    INNOVATION_KWS = ["from scratch", "novel", "innovative", "designed", "architected", "refactored", "optimized", "patent"]
    IMPACT_KWS = ["reduced", "improved", "boosted", "optimized", "increased", "saved", "accelerated", "growth", "%", "percent", "latency", "conversion", "revenue"]

    DEPLOY_KWS = ["kubernetes", "docker", "ci/cd", "jenkins", "github actions", "gitlab", "deploy", "pipeline", "ansible", "terraform", "ecs", "eks"]
    AI_KWS = ["llm", "machine learning", "pytorch", "tensorflow", "gpt", "nlp", "vision", "ai", "openai", "bert", "scikit-learn", "deep learning", "neural"]
    CLOUD_KWS = ["aws", "gcp", "azure", "cloud", "s3", "ec2", "rds", "lambda", "serverless"]
    SECURITY_KWS = ["jwt", "oauth", "auth", "security", "cryptography", "encryption", "ssl", "iam", "vulnerability", "pen-testing"]

    def analyze(self, profile: CandidateProfile) -> Dict[str, Any]:
        projects_analysis = []
        overall_project_score = 0.0

        for p in profile.projects:
            desc = p.description or ""
            resps = " ".join(p.responsibilities)
            corpus = f"{p.name} {desc} {' '.join(p.technologies)} {resps}".lower()

            # 1. Complexity
            complexity_hits = [kw for kw in self.COMPLEXITY_KWS if kw in corpus]
            complexity = "High" if len(complexity_hits) >= 3 else "Medium" if len(complexity_hits) >= 1 else "Low"

            # 2. Scale
            scale_hits = [kw for kw in self.SCALE_KWS if kw in corpus]
            scale = "High" if len(scale_hits) >= 2 else "Medium" if len(scale_hits) >= 1 else "Low"

            # 3. Ownership
            ownership = "Contributor"
            ownership_score = 10
            if any(kw in corpus for kw in self.OWNERSHIP_LEAD_KWS):
                ownership = "Lead / Owner"
                ownership_score = 25
            elif any(kw in corpus for kw in self.OWNERSHIP_CORE_KWS):
                ownership = "Core Contributor"
                ownership_score = 20

            # 4. Indicators
            has_leadership = any(kw in corpus for kw in ["led", "spearheaded", "mentored", "managed", "ownership"])
            has_innovation = any(kw in corpus for kw in self.INNOVATION_KWS)
            has_impact = any(kw in corpus for kw in self.IMPACT_KWS)

            has_deploy = any(kw in corpus for kw in self.DEPLOY_KWS)
            has_ai = any(kw in corpus for kw in self.AI_KWS)
            has_cloud = any(kw in corpus for kw in self.CLOUD_KWS)
            has_security = any(kw in corpus for kw in self.SECURITY_KWS)

            # 5. Project Score Calculation (0-100)
            score = 40.0 # base score
            # Tech count weight
            score += min(15.0, len(p.technologies) * 2)
            # Complexity weight
            score += 20.0 if complexity == "High" else 10.0 if complexity == "Medium" else 5.0
            # Scale weight
            score += 15.0 if scale == "High" else 10.0 if scale == "Medium" else 5.0
            # Ownership weight
            score += ownership_score
            # Boosts for indicators
            if has_leadership: score += 5.0
            if has_innovation: score += 5.0
            if has_impact: score += 5.0
            if has_deploy: score += 5.0
            if has_ai: score += 5.0
            if has_cloud: score += 5.0
            if has_security: score += 5.0

            score = min(100.0, score)

            # Evidence collection
            evidence = {
                "leadership": [kw for kw in ["led", "spearheaded", "mentored", "managed", "ownership"] if kw in corpus],
                "innovation": [kw for kw in self.INNOVATION_KWS if kw in corpus],
                "impact": [kw for kw in self.IMPACT_KWS if kw in corpus],
                "cloud": [kw for kw in self.CLOUD_KWS if kw in corpus],
                "deployment": [kw for kw in self.DEPLOY_KWS if kw in corpus],
                "security": [kw for kw in self.SECURITY_KWS if kw in corpus],
                "ai": [kw for kw in self.AI_KWS if kw in corpus]
            }

            projects_analysis.append({
                "project_name": p.name,
                "domain": p.domain or "General / Multi-domain",
                "complexity": complexity,
                "scale": scale,
                "ownership": ownership,
                "technologies": p.technologies,
                "has_leadership": bool(has_leadership),
                "has_innovation": bool(has_innovation),
                "has_impact": bool(has_impact),
                "deployment_experience": bool(has_deploy),
                "ai_experience": bool(has_ai),
                "cloud_usage": bool(has_cloud),
                "security_awareness": bool(has_security),
                "evidence": evidence,
                "project_score": float(round(score, 1)),
                "confidence_score": float(0.85 if len(p.technologies) > 2 else 0.70)
            })

        if projects_analysis:
            overall_project_score = sum(pa["project_score"] for pa in projects_analysis) / len(projects_analysis)

        return {
            "projects": projects_analysis,
            "average_project_score": float(round(overall_project_score, 1))
        }

project_analyzer = ProjectAnalyzer()
