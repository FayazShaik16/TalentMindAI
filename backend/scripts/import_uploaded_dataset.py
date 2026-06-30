import sys
import os
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import get_db_session
from app.services.dataset_management_service import dataset_mgmt_service

async def main():
    print("Resetting database to clear old seeds/empty metadata...")
    async for db in get_db_session():
        await dataset_mgmt_service.reset_dataset(db)
        print("Database reset completed.")

    file_path = "uploads/candidates.jsonl"
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found in uploads folder.")
        return

    print("Running candidates.jsonl import pipeline (processing all 100,000 candidates)...")
    await dataset_mgmt_service.import_pipeline(file_path, "candidates.jsonl")
    print("Import pipeline completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
