from sqlalchemy.ext.asyncio import AsyncSession
from app.database.repositories.base import BaseRepository
from app.database.models.candidate_intelligence import CandidateIntelligence

class CandidateIntelligenceRepository(BaseRepository[CandidateIntelligence]):
    def __init__(self, session: AsyncSession):
        super().__init__(CandidateIntelligence, session)

    async def get_candidate_intelligence(self, candidate_id: str) -> CandidateIntelligence | None:
        """
        Fetch candidate intelligence by Candidate ID.
        """
        return await self.get_by_id(candidate_id)

    async def upsert_candidate_intelligence(self, intel: CandidateIntelligence) -> CandidateIntelligence:
        """
        Upsert a candidate intelligence record.
        """
        db_intel = await self.get_candidate_intelligence(intel.candidate_id)
        if not db_intel:
            self.session.add(intel)
            db_intel = intel
        else:
            db_intel.professional_summary = intel.professional_summary
            db_intel.career_intelligence = intel.career_intelligence
            db_intel.technical_intelligence = intel.technical_intelligence
            db_intel.leadership_intelligence = intel.leadership_intelligence
            db_intel.project_intelligence = intel.project_intelligence
            db_intel.domain_intelligence = intel.domain_intelligence
            db_intel.career_growth = intel.career_growth
            db_intel.specializations = intel.specializations
            db_intel.knowledge_graph = intel.knowledge_graph
            db_intel.trace = intel.trace
            db_intel.confidence_scores = intel.confidence_scores
            self.session.add(db_intel)

        await self.session.flush()
        return db_intel
