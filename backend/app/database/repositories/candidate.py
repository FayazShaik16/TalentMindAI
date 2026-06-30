import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.repositories.base import BaseRepository
from app.database.models.candidate import (
    Candidate, Experience, Project, Education, Skill,
    Certification, CandidateMetadata, EngineeredFeature
)
from app.schemas.candidate import CandidateProfile

class CandidateRepository(BaseRepository[Candidate]):
    def __init__(self, session: AsyncSession):
        super().__init__(Candidate, session)

    async def get_candidate_profile(self, candidate_id: str) -> Candidate | None:
        """
        Fetch a Candidate profile preloaded with related experiences, projects, skills, etc.
        """
        return await self.get_by_id(candidate_id)

    async def upsert_candidate_profile(self, profile: CandidateProfile) -> Candidate:
        """
        Upserts a candidate profile, recreating associated child models under delete-orphan cascade constraints.
        """
        db_cand = await self.get_candidate_profile(profile.id)

        # Parse children models
        experiences = [Experience(**exp.model_dump()) for exp in profile.experiences]
        projects = [Project(**proj.model_dump()) for proj in profile.projects]
        educations = [Education(**edu.model_dump()) for edu in profile.educations]
        skills = [Skill(**skill.model_dump()) for skill in profile.skills]
        certifications = [Certification(**cert.model_dump()) for cert in profile.certifications]

        metadata_record = CandidateMetadata(**profile.metadata.model_dump())
        features = EngineeredFeature(**profile.engineered_features.model_dump())

        if not db_cand:
            # Create a completely new Candidate
            db_cand = Candidate(
                id=profile.id,
                first_name=profile.personal_info.first_name,
                last_name=profile.personal_info.last_name,
                email=profile.personal_info.email,
                phone=profile.personal_info.phone,
                location=profile.personal_info.location,
                experiences=experiences,
                projects=projects,
                educations=educations,
                skills=skills,
                certifications=certifications,
                metadata_record=metadata_record,
                features=features,
            )
            self.session.add(db_cand)
        else:
            # Update scalars
            db_cand.first_name = profile.personal_info.first_name
            db_cand.last_name = profile.personal_info.last_name
            db_cand.email = profile.personal_info.email
            db_cand.phone = profile.personal_info.phone
            db_cand.location = profile.personal_info.location

            # Flush relations: SQLAlchemy cleans up orphaned rows automatically
            db_cand.experiences.clear()
            db_cand.experiences.extend(experiences)

            db_cand.projects.clear()
            db_cand.projects.extend(projects)

            db_cand.educations.clear()
            db_cand.educations.extend(educations)

            db_cand.skills.clear()
            db_cand.skills.extend(skills)

            db_cand.certifications.clear()
            db_cand.certifications.extend(certifications)

            if db_cand.metadata_record:
                for k, v in profile.metadata.model_dump().items():
                    setattr(db_cand.metadata_record, k, v)
            else:
                db_cand.metadata_record = metadata_record

            if db_cand.features:
                for k, v in profile.engineered_features.model_dump().items():
                    setattr(db_cand.features, k, v)
            else:
                db_cand.features = features

            self.session.add(db_cand)

        await self.session.flush()
        return db_cand

    async def get_dataset_analytics(self) -> dict:
        """
        Queries statistical aggregations (totals, averages, top skills/tech stacks).
        """
        # Count total candidates
        total_count = await self.session.scalar(select(func.count(Candidate.id))) or 0

        # Average experience and tenure
        avg_exp = await self.session.scalar(select(func.avg(EngineeredFeature.years_experience))) or 0.0
        avg_tenure = await self.session.scalar(select(func.avg(EngineeredFeature.average_tenure))) or 0.0

        # Top 10 skills
        skill_query = select(
            Skill.normalized_name,
            func.count(Skill.id).label("count")
        ).group_by(Skill.normalized_name).order_by(func.count(Skill.id).desc()).limit(10)

        skill_result = await self.session.execute(skill_query)
        top_skills = [
            {"skill": row[0], "count": row[1]}
            for row in skill_result.all()
            if row[0] is not None
        ]

        # Top 10 technologies (accumulated locally to support SQLite fallback)
        proj_query = select(Project.technologies)
        proj_result = await self.session.execute(proj_query)
        tech_counts = {}
        for row in proj_result.scalars().all():
            for tech in row:
                t_clean = tech.strip()
                if t_clean:
                    tech_counts[t_clean] = tech_counts.get(t_clean, 0) + 1

        top_techs = sorted(
            [{"technology": k, "count": v} for k, v in tech_counts.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:10]

        return {
            "total_candidates": total_count,
            "average_experience_years": round(float(avg_exp), 2),
            "average_tenure_years": round(float(avg_tenure), 2),
            "top_skills": top_skills,
            "top_technologies": top_techs,
        }
