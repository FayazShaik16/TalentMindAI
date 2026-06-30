import asyncio
from app.database.session import engine
from app.database.models.base import Base
import app.database.models.candidate
import app.database.models.job
import app.database.models.candidate_intelligence
import app.database.models.candidate_evidence
import app.database.models.ranking
import app.database.models.explanation
import app.database.models.workspace
import app.database.models.dataset_management

async def init_db():
    print("Creating all tables in target database...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully.")

if __name__ == "__main__":
    asyncio.run(init_db())
