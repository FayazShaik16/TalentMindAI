import re
from typing import Any, Dict, List
from app.schemas.candidate import CandidateProfile

class SpecializationEngine:
    """
    Classifies candidate into one or more engineering roles (Backend, Frontend, Full Stack,
    DevOps, AI, ML, Data, Cloud, Mobile, Security, Blockchain, Architect, Engineering Manager)
    based on tech stacks, responsibilities, and job titles.
    """

    ROLE_KWS = {
        "Backend Engineer": ["django", "flask", "fastapi", "spring", "backend", "express", "node", "nest", "rails", "postgres", "mysql", "mongodb", "redis", "sql", "api", "rest", "graphql", "microservices", "java", "golang", "go", "python", "c#"],
        "Frontend Engineer": ["react", "angular", "vue", "frontend", "html", "css", "sass", "tailwind", "next.js", "nextjs", "javascript", "typescript", "jquery", "bootstrap"],
        "DevOps": ["docker", "kubernetes", "k8s", "terraform", "ansible", "jenkins", "gitlab ci", "github actions", "helm", "devops", "ci/cd", "pipeline"],
        "Cloud Engineer": ["aws", "gcp", "azure", "cloud", "lambda", "serverless", "s3", "ec2", "rds", "cloudformation", "iam"],
        "AI Engineer": ["llm", "nlp", "artificial intelligence", "gpt", "openai", "langchain", "prompt engineering", "transformers", "huggingface", "generative ai"],
        "Data Engineer": ["spark", "hadoop", "etl", "data pipeline", "kafka", "rabbitmq", "cassandra", "redshift", "bigquery", "data lake", "data warehouse"],
        "ML Engineer": ["pytorch", "tensorflow", "scikit-learn", "machine learning", "deep learning", "neural network", "pandas", "numpy", "keras"],
        "Blockchain Engineer": ["ethereum", "solidity", "smart contract", "web3", "blockchain", "dapp", "hyperledger", "rust", "cryptography"],
        "Security Engineer": ["cybersecurity", "penetration", "cryptography", "iam", "oauth", "compliance", "owasp", "security", "firewall", "vulnerability", "jwt"],
        "Mobile Engineer": ["react native", "flutter", "ios", "android", "swift", "kotlin", "mobile", "objc", "xcode"],
        "Architect": ["system design", "architect", "architecture", "clean architecture", "design patterns", "infrastructure design", "monolithic", "microservices"],
        "Engineering Manager": ["lead", "manager", "team lead", "supervisor", "vp", "chief", "director", "head of", "product manager", "scrum master"]
    }

    def analyze(self, profile: CandidateProfile) -> Dict[str, Any]:
        experiences = profile.experiences
        projects = profile.projects
        skills = profile.skills

        # Build clean lowercase text corpus
        skills_str = " ".join([s.normalized_name or s.name for s in skills])
        exp_titles_str = " ".join([e.job_title for e in experiences])
        exp_desc_str = " ".join([e.description or "" for e in experiences])
        proj_tech_str = " ".join([" ".join(p.technologies) for p in projects])
        proj_resp_str = " ".join([" ".join(p.responsibilities) for p in projects])
        
        corpus = f"{skills_str} {exp_titles_str} {exp_desc_str} {proj_tech_str} {proj_resp_str}".lower()

        scores = {}
        for role, keywords in self.ROLE_KWS.items():
            matches = 0
            for kw in keywords:
                # Use word boundaries or literal checks
                if kw in corpus:
                    # boost if found in job titles
                    if kw in exp_titles_str.lower():
                        matches += 3
                    else:
                        matches += 1

            # Normalize match score between 0.0 and 1.0
            score = min(1.0, float(matches / 6.0)) if matches > 0 else 0.0
            scores[role] = float(round(score, 2))

        # Handle Full Stack logic
        # Full stack if both frontend and backend are high
        be_score = scores.get("Backend Engineer", 0.0)
        fe_score = scores.get("Frontend Engineer", 0.0)
        
        if be_score > 0.4 and fe_score > 0.4:
            scores["Full Stack"] = float(round((be_score + fe_score) / 2.0, 2))
        else:
            scores["Full Stack"] = 0.0

        # Filter out roles with score > 0.35 as qualified specializations
        specializations = []
        for role, score in scores.items():
            if score > 0.35:
                specializations.append(role)

        # Fallback if none found
        if not specializations:
            # Pick highest score
            highest_role = max(scores, key=scores.get)
            if scores[highest_role] > 0.0:
                specializations.append(highest_role)
            else:
                specializations.append("Full Stack") # Default fallback

        return {
            "scores": scores,
            "specializations": specializations
        }

specialization_engine = SpecializationEngine()
