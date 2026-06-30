import os
import json
import sqlite3
import hashlib
import time
from typing import Any
from collections.abc import Sequence

from app.core.config.config import settings
from app.core.logging.logging import logger
from app.schemas.candidate import CandidateProfile
from app.providers.embedding.local import LocalEmbeddingProvider

class EmbeddingService:
    """
    Manages text representation formatting, persistent SQLite caching,
    incremental updates, and batch embedding calls.
    """
    def __init__(self):
        self.cache_dir = settings.EMBEDDING_CACHE_DIR
        os.makedirs(self.cache_dir, exist_ok=True)
        self.db_path = os.path.join(self.cache_dir, "embeddings_cache.db")
        self._init_db()
        self._provider = None

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                    candidate_id TEXT NOT NULL,
                    embedding_type TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    embedding TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (candidate_id, embedding_type)
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    @property
    def provider(self) -> LocalEmbeddingProvider:
        """
        Lazily loads and returns the configured embedding provider.
        """
        if self._provider is None:
            # Local is the default and only active provider currently
            self._provider = LocalEmbeddingProvider()
        return self._provider

    def _get_string_hash(self, text: str) -> str:
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    async def get_cached_embedding(
        self, candidate_id: str, embedding_type: str, current_hash: str
    ) -> list[float] | None:
        """
        Retrieves cached embedding if the payload hash matches current_hash.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            try:
                cursor = conn.execute(
                    "SELECT payload_hash, embedding FROM cache WHERE candidate_id = ? AND embedding_type = ?",
                    (candidate_id, embedding_type)
                )
                row = cursor.fetchone()
                if row and row["payload_hash"] == current_hash:
                    return json.loads(row["embedding"])
            finally:
                conn.close()
        except Exception as e:
            logger.error("cache_read_failed", candidate_id=candidate_id, error=str(e))
        return None

    async def cache_embedding(
        self, candidate_id: str, embedding_type: str, current_hash: str, embedding: list[float]
    ):
        """
        Persists generated embedding vector in SQLite cache.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO cache (candidate_id, embedding_type, payload_hash, embedding, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (candidate_id, embedding_type, current_hash, json.dumps(embedding))
                )
                conn.commit()
            finally:
                conn.close()
        except Exception as e:
            logger.error("cache_write_failed", candidate_id=candidate_id, error=str(e))

    def format_text(self, candidate: CandidateProfile, embedding_type: str) -> str:
        """
        Serializes specific components of a Candidate profile into clean text representations.
        """
        if embedding_type == "summary":
            skills_str = ", ".join([s.normalized_name or s.name for s in candidate.skills])
            exp_titles = ", ".join([e.job_title for e in candidate.experiences])
            return (
                f"Candidate: {candidate.personal_info.first_name} {candidate.personal_info.last_name}. "
                f"Location: {candidate.personal_info.location or 'Unknown'}. "
                f"Experience Titles: {exp_titles}. "
                f"Skills: {skills_str}."
            ).strip()

        elif embedding_type == "career":
            career_segments = []
            for exp in candidate.experiences:
                current = "Present" if exp.is_current else exp.end_date or "Unknown"
                desc = exp.description or ""
                career_segments.append(
                    f"Role: {exp.job_title} at {exp.company_name} (From {exp.start_date} to {current}). {desc}"
                )
            return " ".join(career_segments) if career_segments else "No career history recorded."

        elif embedding_type == "projects":
            proj_segments = []
            for p in candidate.projects:
                techs = ", ".join(p.technologies)
                resps = " ".join(p.responsibilities)
                proj_segments.append(
                    f"Project: {p.name}. Domain: {p.domain or 'General'}. Tech: {techs}. Details: {p.description or ''}. Responsibilities: {resps}"
                )
            return " ".join(proj_segments) if proj_segments else "No projects recorded."

        elif embedding_type == "skills":
            skills_segments = []
            for s in candidate.skills:
                path = ", ".join(s.hierarchy_path)
                skills_segments.append(f"Skill: {s.normalized_name or s.name} (Category: {s.category or 'Other'}, Path: {path})")
            return " ".join(skills_segments) if skills_segments else "No skills recorded."

        elif embedding_type == "education":
            edu_segments = []
            for edu in candidate.educations:
                edu_segments.append(
                    f"Degree: {edu.degree or 'Degree'} in {edu.field_of_study or 'General'} from {edu.institution} (Ended: {edu.end_date or 'Unknown'})"
                )
            return " ".join(edu_segments) if edu_segments else "No education recorded."

        elif embedding_type == "behavior":
            # Future ready behavioral placeholder
            stability = candidate.behavior_signals.career_stability_score
            tenure = candidate.behavior_signals.average_tenure_years
            return f"Average Tenure: {tenure} years. Career Stability Score: {stability}."

        return ""

    async def get_candidate_embeddings(
        self, candidate: CandidateProfile, force: bool = False
    ) -> dict[str, list[float]]:
        """
        Resolves candidate sub-embeddings (summary, career, projects, skills, education)
        through incremental hash checks against cached data.
        """
        embedding_types = ["summary", "career", "projects", "skills", "education"]
        results = {}

        # 1. Compute hashes and check cache
        needed_types = []
        needed_texts = []

        for e_type in embedding_types:
            text = self.format_text(candidate, e_type)
            p_hash = self._get_string_hash(text)

            if not force:
                cached_vec = await self.get_cached_embedding(candidate.id, e_type, p_hash)
                if cached_vec:
                    results[e_type] = cached_vec
                    continue

            needed_types.append((e_type, p_hash))
            needed_texts.append(text)

        # 2. Call embedding provider for miss items
        if needed_texts:
            logger.info(
                "generating_embeddings",
                candidate_id=candidate.id,
                types=[t[0] for t in needed_types]
            )
            # Batch embedding generation
            vectors = await self.provider.embed_documents(needed_texts)
            for (e_type, p_hash), vec in zip(needed_types, vectors):
                results[e_type] = vec
                # Cache it
                await self.cache_embedding(candidate.id, e_type, p_hash, vec)

        return results

    async def get_job_embeddings(
        self, job_id: str, profile: dict, hidden_reqs: dict, raw_text: str, force: bool = False
    ) -> dict[str, list[float]]:
        """
        Generates and caches 6 different embeddings representing various dimensions of the job description.
        """
        embedding_types = ["overall", "skills", "responsibilities", "behavior", "experience", "technology_stack"]
        results = {}

        # Format components to capture specific intent dimensions
        skills_str = ", ".join(profile.get("skills", {}).get("primary_skills", []) + profile.get("skills", {}).get("secondary_skills", []))
        resp_snippets = ". ".join([d.get("evidence", "") for d in hidden_reqs.values() if d.get("evidence")])
        behavior_str = ", ".join([f"{k} (confidence {v.get('confidence_score')})" for k, v in hidden_reqs.items()])
        exp_str = f"Required Experience: {profile.get('experience_required_years')} years. Seniority: {profile.get('seniority')}."
        tech_list = []
        for cat in ["programming_languages", "tools", "frameworks", "cloud_platforms"]:
            tech_list.extend(profile.get("skills", {}).get(cat, []))
        tech_str = ", ".join(tech_list)

        texts = {
            "overall": raw_text.strip(),
            "skills": f"Skills: {skills_str}" if skills_str else "No skills specified.",
            "responsibilities": f"Responsibilities: {resp_snippets}" if resp_snippets else "No core responsibilities inferred.",
            "behavior": f"Required Behaviors: {behavior_str}" if behavior_str else "No explicit behavioral expectations.",
            "experience": exp_str,
            "technology_stack": f"Tech Stack: {tech_str}" if tech_str else "No technology stack specified."
        }

        needed_types = []
        needed_texts = []

        for e_type in embedding_types:
            text = texts[e_type]
            p_hash = self._get_string_hash(text)
            db_id = f"job_{job_id}"

            if not force:
                cached_vec = await self.get_cached_embedding(db_id, e_type, p_hash)
                if cached_vec:
                    results[e_type] = cached_vec
                    continue

            needed_types.append((e_type, p_hash))
            needed_texts.append(text)

        if needed_texts:
            logger.info(
                "generating_job_embeddings",
                job_id=job_id,
                types=[t[0] for t in needed_types]
            )
            # Batch embedding generation
            vectors = await self.provider.embed_documents(needed_texts)
            for (e_type, p_hash), vec in zip(needed_types, vectors):
                results[e_type] = vec
                db_id = f"job_{job_id}"
                # Cache it
                await self.cache_embedding(db_id, e_type, p_hash, vec)

        return results

    async def embed_job_description(self, job_desc: str) -> list[float]:
        """
        Embeds a raw job description using the provider.
        """
        return await self.provider.embed_query(job_desc)

    async def embed_recruiter_query(self, query: str) -> list[float]:
        """
        Embeds a raw search query using the provider.
        """
        return await self.provider.embed_query(query)

    async def get_candidate_intelligence_embeddings(
        self, candidate_id: str, texts: dict[str, str], force: bool = False
    ) -> dict[str, list[float]]:
        """
        Generates and caches 8 distinct embeddings representing various dimensions of the Candidate Intelligence Profile.
        """
        results = {}
        needed_types = []
        needed_texts = []

        for e_type, text in texts.items():
            p_hash = self._get_string_hash(text)
            db_id = f"cand_intel_{candidate_id}"

            if not force:
                cached_vec = await self.get_cached_embedding(db_id, e_type, p_hash)
                if cached_vec:
                    results[e_type] = cached_vec
                    continue

            needed_types.append((e_type, p_hash))
            needed_texts.append(text)

        if needed_texts:
            logger.info(
                "generating_candidate_intelligence_embeddings",
                candidate_id=candidate_id,
                types=[t[0] for t in needed_types]
            )
            # Batch embedding generation
            vectors = await self.provider.embed_documents(needed_texts)
            for (e_type, p_hash), vec in zip(needed_types, vectors):
                results[e_type] = vec
                db_id = f"cand_intel_{candidate_id}"
                # Cache it
                await self.cache_embedding(db_id, e_type, p_hash, vec)

        return results

    def clear_cache(self) -> bool:
        """
        Clears cache table.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute("DELETE FROM cache")
                conn.commit()
            finally:
                conn.close()
            return True
        except Exception as e:
            logger.error("cache_clear_failed", error=str(e))
            return False

embedding_service = EmbeddingService()
