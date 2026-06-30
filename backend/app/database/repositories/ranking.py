from sqlalchemy.ext.asyncio import AsyncSession
from app.database.repositories.base import BaseRepository
from app.database.models.ranking import JobCandidateRanking

class RankingRepository(BaseRepository[JobCandidateRanking]):
    def __init__(self, session: AsyncSession):
        super().__init__(JobCandidateRanking, session)

    async def get_ranking(self, job_id: str) -> JobCandidateRanking | None:
        """
        Fetch ranking profile by Job ID.
        """
        return await self.get_by_id(job_id)

    async def upsert_ranking(self, ranking: JobCandidateRanking) -> JobCandidateRanking:
        """
        Upsert a job candidate ranking record.
        """
        db_ranking = await self.get_ranking(ranking.job_id)
        if not db_ranking:
            self.session.add(ranking)
            db_ranking = ranking
        else:
            db_ranking.rankings = ranking.rankings
            db_ranking.trace = ranking.trace
            db_ranking.statistics = ranking.statistics
            self.session.add(db_ranking)
        
        await self.session.flush()
        return db_ranking
