from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.repositories.base import BaseRepository
from app.database.models.workspace import RecruiterWorkspace, JobSession, RecruiterActivity

class WorkspaceRepository(BaseRepository[RecruiterWorkspace]):
    def __init__(self, session: AsyncSession):
        super().__init__(RecruiterWorkspace, session)

    async def get_workspace(self, recruiter_id: str) -> RecruiterWorkspace | None:
        result = await self.session.execute(
            select(RecruiterWorkspace).where(RecruiterWorkspace.recruiter_id == recruiter_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create_workspace(self, recruiter_id: str) -> RecruiterWorkspace:
        ws = await self.get_workspace(recruiter_id)
        if not ws:
            ws = RecruiterWorkspace(
                recruiter_id=recruiter_id,
                preferences={},
                search_history=[],
                saved_candidates=[],
                saved_jobs=[],
                folders={},
                tags={},
                notes={}
            )
            self.session.add(ws)
            await self.session.flush()
        return ws

    async def save_workspace(self, workspace: RecruiterWorkspace) -> RecruiterWorkspace:
        self.session.add(workspace)
        await self.session.flush()
        return workspace

    async def get_session(self, session_id: str) -> JobSession | None:
        result = await self.session.execute(
            select(JobSession).where(JobSession.session_id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_all_sessions_for_job(self, job_id: str) -> list[JobSession]:
        result = await self.session.execute(
            select(JobSession).where(JobSession.job_id == job_id)
        )
        return list(result.scalars().all())

    async def get_all_sessions(self) -> list[JobSession]:
        result = await self.session.execute(
            select(JobSession)
        )
        return list(result.scalars().all())

    async def upsert_session(self, session: JobSession) -> JobSession:
        db_sess = await self.get_session(session.session_id)
        if not db_sess:
            self.session.add(session)
            db_sess = session
        else:
            db_sess.ranking_version = session.ranking_version
            db_sess.candidate_snapshot = session.candidate_snapshot
            db_sess.ai_version = session.ai_version
            db_sess.status = session.status
            db_sess.history = session.history
            self.session.add(db_sess)
        await self.session.flush()
        return db_sess

    async def log_activity(self, recruiter_id: str, action_type: str, details: dict, duration_ms: int = 0) -> RecruiterActivity:
        activity = RecruiterActivity(
            recruiter_id=recruiter_id,
            action_type=action_type,
            details=details,
            duration_ms=duration_ms
        )
        self.session.add(activity)
        await self.session.flush()
        return activity

    async def get_activities(self, recruiter_id: str | None = None, limit: int = 100) -> list[RecruiterActivity]:
        stmt = select(RecruiterActivity)
        if recruiter_id:
            stmt = stmt.where(RecruiterActivity.recruiter_id == recruiter_id)
        stmt = stmt.order_by(RecruiterActivity.id.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
