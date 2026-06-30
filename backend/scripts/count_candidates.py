import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import get_db_session
from app.database.repositories.candidate import CandidateRepository

async def main():
    async for db in get_db_session():
        repo = CandidateRepository(db)
        candidates = await repo.get_all()
        print(f"TOTAL_CANDIDATES_IN_DB: {len(candidates)}")

if __name__ == "__main__":
    asyncio.run(main())
