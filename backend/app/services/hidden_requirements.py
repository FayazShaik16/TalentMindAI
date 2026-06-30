import re
import numpy as np
from typing import Dict, Any, List
from app.services.embedding_service import embedding_service
from app.core.logging.logging import logger

class HiddenRequirementDetector:
    """
    Detects hidden, implied recruiter expectations from unstructured JDs
    using keyword extraction and sentence-level semantic similarity.
    Provides evidence-backed confidence scores.
    """

    EXPECTATIONS = {
        "Leadership": {
            "keywords": [r"lead", r"manage", r"direct", r"head", r"steer", r"champion", r"coordinate"],
            "description": "Coordinate or lead projects, initiatives, or technology directions."
        },
        "Ownership": {
            "keywords": [r"ownership", r"end-to-end", r"driver", r"autonomy", r"take charge", r"accountable", r"self-starter"],
            "description": "Take full responsibility and drive products or components from inception to production."
        },
        "Mentorship": {
            "keywords": [r"mentor", r"coach", r"guide", r"teach", r"advise", r"develop team", r"junior engineers", r"onboard"],
            "description": "Guide, train, or coach junior or mid-level team members."
        },
        "System Design": {
            "keywords": [r"system design", r"architecture", r"high-level design", r"architectural patterns", r"modular design", r"distributed systems"],
            "description": "Architect and design complex, modular, and maintainable software architectures."
        },
        "Scalability": {
            "keywords": [r"scale", r"scalability", r"high throughput", r"low latency", r"performance optimization", r"distributed systems", r"concurrency"],
            "description": "Build high-performance, high-traffic systems capable of scaling efficiently."
        },
        "Customer Interaction": {
            "keywords": [r"customer", r"client", r"stakeholder", r"user feedback", r"product requirements", r"business needs", r"external partner"],
            "description": "Work directly with clients, customers, or external business stakeholders."
        },
        "Research": {
            "keywords": [r"research", r"experiment", r"novel", r"state-of-the-art", r"academic", r"publication", r"deep dive", r"exploration"],
            "description": "Investigate new technologies, conduct experiments, or work on R&D initiatives."
        },
        "Startup Experience": {
            "keywords": [r"startup", r"fast-paced", r"dynamic", r"ambiguous", r"wear many hats", r"greenfield", r"rapid iteration"],
            "description": "Thrive in high-growth, fast-paced, and unstructured startup environments."
        },
        "Enterprise Experience": {
            "keywords": [r"enterprise", r"scale", r"compliance", r"large-scale deployment", r"legacy migration", r"governance", r"corporate"],
            "description": "Work with complex organizational compliance, security, and governance standards."
        },
        "Product Thinking": {
            "keywords": [r"product vision", r"product thinking", r"user experience", r"ux", r"product roadmap", r"features", r"business impact"],
            "description": "Align engineering tasks with user satisfaction, product metrics, and business outcomes."
        },
        "Cross-functional Collaboration": {
            "keywords": [r"cross-functional", r"collaboration", r"collaborate with", r"product managers", r"designers", r"operations", r"product team"],
            "description": "Work effectively with designers, product managers, marketing, and business operations teams."
        }
    }

    def __init__(self):
        self._expectation_embeddings = {}

    def _split_into_sentences(self, text: str) -> List[str]:
        # Split by periods, question marks, exclamation marks followed by whitespace
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if len(s.strip()) > 10]

    async def detect(self, job_description: str) -> Dict[str, Dict[str, Any]]:
        """
        Scan a job description, identify evidence for expectations,
        and assign confidence scores based on semantic similarity.
        """
        results = {}
        sentences = self._split_into_sentences(job_description)
        if not sentences:
            return {}

        try:
            # Precompute embeddings for JD sentences
            sentence_vectors = await embedding_service.provider.embed_documents(sentences)
            
            # Precompute embeddings for expectations descriptions
            if not self._expectation_embeddings:
                keys = list(self.EXPECTATIONS.keys())
                descriptions = [self.EXPECTATIONS[k]["description"] for k in keys]
                desc_vectors = await embedding_service.provider.embed_documents(descriptions)
                self._expectation_embeddings = dict(zip(keys, desc_vectors))

            for exp_name, exp_data in self.EXPECTATIONS.items():
                keywords = exp_data["keywords"]
                exp_vector = self._expectation_embeddings[exp_name]

                best_evidence = None
                max_keyword_matches = 0
                max_semantic_similarity = 0.0

                # Search through sentences for evidence
                for s, s_vector in zip(sentences, sentence_vectors):
                    # 1. Count keyword matches
                    kw_matches = sum(1 for kw in keywords if re.search(kw, s, re.IGNORECASE))
                    
                    # 2. Compute similarity
                    dot_product = np.dot(s_vector, exp_vector)
                    norm_s = np.linalg.norm(s_vector)
                    norm_e = np.linalg.norm(exp_vector)
                    similarity = float(dot_product / (norm_s * norm_e) if norm_s > 0 and norm_e > 0 else 0.0)

                    if kw_matches > 0 or similarity > 0.5:
                        # Determine if this sentence is the best evidence
                        score = similarity + (0.2 * kw_matches)
                        current_best_score = max_semantic_similarity + (0.2 * max_keyword_matches)
                        
                        if score > current_best_score:
                            best_evidence = s
                            max_keyword_matches = kw_matches
                            max_semantic_similarity = similarity

                # Compute final confidence score
                if best_evidence:
                    # Base score from semantic similarity
                    confidence = float(max_semantic_similarity)
                    
                    # Boost score if keywords were explicitly matched
                    if max_keyword_matches > 0:
                        confidence += 0.15 * min(3, max_keyword_matches)
                        
                    # Bound between 0.0 and 0.99
                    confidence = min(0.99, max(0.0, confidence))
                    
                    # Only include if confidence is above a threshold
                    if confidence >= 0.50:
                        results[exp_name] = {
                            "evidence": best_evidence,
                            "confidence_score": round(float(confidence), 2)
                        }
                else:
                    # Fallback default: not detected (score = 0.0)
                    pass

        except Exception as e:
            logger.error("hidden_requirements_detection_failed", error=str(e))
            # Fallback to pure regex search
            for exp_name, exp_data in self.EXPECTATIONS.items():
                keywords = exp_data["keywords"]
                for s in sentences:
                    kw_matches = sum(1 for kw in keywords if re.search(kw, s, re.IGNORECASE))
                    if kw_matches > 0:
                        results[exp_name] = {
                            "evidence": s,
                            "confidence_score": round(0.5 + 0.1 * min(3, kw_matches), 2)
                        }
                        break

        return results

hidden_detector = HiddenRequirementDetector()
