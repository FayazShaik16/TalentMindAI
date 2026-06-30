import sys
import os
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import get_db_session
from app.services.dataset_management_service import dataset_mgmt_service
from app.utils.caching import disk_cache

async def main():
    print("Resetting all database tables (candidates, jobs, sessions, intelligence, evidence)...")
    async for db in get_db_session():
        await dataset_mgmt_service.reset_dataset(db)
        print("Database reset completed successfully.")
        
    print("Clearing disk cache...")
    try:
        disk_cache.clear()
        print("Disk cache cleared.")
    except Exception as e:
        print(f"Could not clear disk cache: {e}")

    print("\nSystem cleared for a fresh start! The database and cache are now empty.")

if __name__ == "__main__":
    asyncio.run(main())
