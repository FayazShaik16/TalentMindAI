from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.repositories.base import BaseRepository
from app.database.models.explanation import JobCandidateExplanation

class ExplanationRepository(BaseRepository[JobCandidateExplanation]):
    def __init__(self, session: AsyncSession):
        super().__init__(JobCandidateExplanation, session)

    async def get_explanation(self, job_id: str, candidate_id: str) -> JobCandidateExplanation | None:
        """
        Fetch explanation by Job ID and Candidate ID.
        """
        result = await self.session.execute(
            select(JobCandidateExplanation).where(
                JobCandidateExplanation.job_id == job_id,
                JobCandidateExplanation.candidate_id == candidate_id
            )
        )
        return result.scalar_one_or_none()

    async def get_all_for_job(self, job_id: str) -> list[JobCandidateExplanation]:
        """
        Fetch all candidate explanations ranked under a job ID.
        """
        result = await self.session.execute(
            select(JobCandidateExplanation).where(
                JobCandidateExplanation.job_id == job_id
            )
        )
        return list(result.scalars().all())

    async def upsert_explanation(self, explanation: JobCandidateExplanation) -> JobCandidateExplanation:
        """
        Upsert a job candidate explanation record.
        """
        db_exp = await self.get_explanation(explanation.job_id, explanation.candidate_id)
        if not db_exp:
            self.session.add(explanation)
            db_exp = explanation
        else:
            db_exp.explanation_package = explanation.explanation_package
            db_exp.match_breakdown = explanation.match_breakdown
            db_exp.audit_trail = explanation.audit_trail
            db_exp.trace = explanation.trace
            self.session.add(db_exp)
            
        await self.session.flush()
        return db_exp
