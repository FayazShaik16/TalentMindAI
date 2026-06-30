from sqlalchemy.ext.asyncio import AsyncSession
from app.database.repositories.base import BaseRepository
from app.database.models.job import JobDescription

class JobRepository(BaseRepository[JobDescription]):
    def __init__(self, session: AsyncSession):
        super().__init__(JobDescription, session)

    async def get_job_description(self, job_id: str) -> JobDescription | None:
        """
        Fetch a job description by ID.
        """
        return await self.get_by_id(job_id)

    async def upsert_job_description(self, job: JobDescription) -> JobDescription:
        """
        Upsert a job description profile.
        """
        db_job = await self.get_job_description(job.id)
        if not db_job:
            self.session.add(job)
            db_job = job
        else:
            db_job.raw_text = job.raw_text
            db_job.title = job.title
            db_job.department = job.department
            db_job.seniority = job.seniority
            db_job.experience_required = job.experience_required
            db_job.employment_type = job.employment_type
            db_job.remote_type = job.remote_type
            db_job.intent_profile = job.intent_profile
            db_job.intent_graph = job.intent_graph
            db_job.trace = job.trace
            db_job.confidence_scores = job.confidence_scores
            self.session.add(db_job)

        await self.session.flush()
        return db_job
