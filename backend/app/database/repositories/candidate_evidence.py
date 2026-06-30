from sqlalchemy.ext.asyncio import AsyncSession
from app.database.repositories.base import BaseRepository
from app.database.models.candidate_evidence import CandidateEvidence

class CandidateEvidenceRepository(BaseRepository[CandidateEvidence]):
    def __init__(self, session: AsyncSession):
        super().__init__(CandidateEvidence, session)

    async def get_candidate_evidence(self, candidate_id: str) -> CandidateEvidence | None:
        """
        Fetch candidate evidence by Candidate ID.
        """
        return await self.get_by_id(candidate_id)

    async def upsert_candidate_evidence(self, evidence: CandidateEvidence) -> CandidateEvidence:
        """
        Upsert candidate evidence.
        """
        db_ev = await self.get_candidate_evidence(evidence.candidate_id)
        if not db_ev:
            self.session.add(evidence)
            db_ev = evidence
        else:
            db_ev.skill_verification = evidence.skill_verification
            db_ev.timeline = evidence.timeline
            db_ev.potential_metrics = evidence.potential_metrics
            db_ev.risk_analysis = evidence.risk_analysis
            db_ev.evidence_graph = evidence.evidence_graph
            db_ev.trace = evidence.trace
            db_ev.confidence_scores = evidence.confidence_scores
            self.session.add(db_ev)

        await self.session.flush()
        return db_ev
