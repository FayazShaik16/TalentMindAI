import sys
import os
import argparse
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.pipeline import pipeline
from app.database.session import get_db_session

async def run_pipeline(filepath: str):
    print(f"Starting pipeline pre-processing for: {filepath}")
    async for db in get_db_session():
        try:
            report = await pipeline.process_dataset(filepath, db)
            print("\n=== Ingestion Pipeline Report ===")
            for k, v in report.items():
                print(f"{k}: {v}")
        except Exception as e:
            print(f"Pipeline failed: {str(e)}")
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Ingest and pre-process dataset.")
    parser.add_argument("--file", required=True, help="Path to raw dataset file.")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Error: File does not exist: {args.file}")
        sys.exit(1)

    asyncio.run(run_pipeline(args.file))

if __name__ == "__main__":
    main()
