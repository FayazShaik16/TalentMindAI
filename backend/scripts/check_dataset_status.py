import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import get_db_session
from app.database.models.dataset_management import Dataset, ImportHistory

async def main():
    async for db in get_db_session():
        from sqlalchemy import select
        res = await db.execute(select(Dataset))
        datasets = res.scalars().all()
        print("--- DATASETS ---")
        for d in datasets:
            print(f"ID: {d.id}, Name: {d.name}, Status: {d.status}, Total Candidates: {d.total_candidates}")
            
        res_hist = await db.execute(select(ImportHistory))
        history = res_hist.scalars().all()
        print("\n--- IMPORT HISTORY ---")
        for h in history:
            print(f"ID: {h.id}, Filename: {h.filename}, Status: {h.status}, Total Records: {h.total_records}, Error: {h.error_message}")

if __name__ == "__main__":
    asyncio.run(main())
