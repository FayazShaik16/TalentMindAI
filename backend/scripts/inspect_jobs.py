import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import get_db_session
from app.database.models.job import JobDescription

async def main():
    async for db in get_db_session():
        from sqlalchemy import select
        res = await db.execute(select(JobDescription).order_by(JobDescription.created_at.desc()))
        jobs = res.scalars().all()
        print("--- JOBS IN DB ---")
        for j in jobs:
            print(f"ID: {j.id}")
            print(f"Title: {j.title}")
            print(f"Created At: {j.created_at}")
            print(f"Snippet: {j.raw_text[:150]}...")
            print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())
