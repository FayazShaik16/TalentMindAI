from datetime import datetime, timezone
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.workspace import JobSession
from app.database.repositories.workspace import WorkspaceRepository

class SessionManager:
    def __init__(self, db: AsyncSession):
        self.repo = WorkspaceRepository(db)

    async def create_or_update_session(self, job_id: str, rankings: List[Dict[str, Any]], ai_version: str = "1.0.0") -> JobSession:
        """
        Creates a new Job Session version with candidate snapshots and logs action history.
        """
        # Find existing sessions for this job to compute next version
        existing = await self.repo.get_all_sessions_for_job(job_id)
        
        next_ver = 1
        if existing:
            # Sort by version
            existing.sort(key=lambda x: x.ranking_version)
            next_ver = existing[-1].ranking_version + 1

        # We generate a unique session_id for this version
        sess_id = f"{job_id}_v{next_ver}"

        # Clean rankings snapshot
        snapshot = []
        for r in rankings:
            snapshot.append({
                "candidate_id": r.get("candidate_id"),
                "overall_score": float(r.get("overall_score", 0.0)),
                "rank": r.get("rank"),
                "recommendation": r.get("recommendation")
            })

        action = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": f"Ranking completed for version {next_ver}",
            "candidates_count": len(rankings)
        }

        history = []
        if next_ver > 1:
            history = list(existing[-1].history)
        history.append(action)

        new_sess = JobSession(
            session_id=sess_id,
            job_id=job_id,
            ranking_version=next_ver,
            candidate_snapshot=snapshot,
            ai_version=ai_version,
            status="ACTIVE",
            history=history
        )

        return await self.repo.upsert_session(new_sess)
