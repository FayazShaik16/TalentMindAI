import sys
import os
import argparse
import asyncio
import json
import csv
from typing import List, Dict, Any
from openpyxl import Workbook

# Fix sys.path to run script from backend folder or scripts folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import async_session_factory
from app.database.repositories.ranking import RankingRepository
from app.database.repositories.job import JobRepository

def export_to_csv(filepath: str, data: List[Dict[str, Any]]):
    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Rank", "Candidate ID", "Overall Score", "Recommendation", "Confidence"])
        for item in data:
            writer.writerow([
                item.get("rank"),
                item.get("candidate_id"),
                item.get("overall_score"),
                item.get("recommendation"),
                item.get("hiring_confidence")
            ])

def export_to_excel(filepath: str, data: List[Dict[str, Any]]):
    wb = Workbook()
    ws = wb.active
    ws.title = "Ranking Results"
    
    # Headers
    ws.append(["Rank", "Candidate ID", "Overall Score", "Recommendation", "Confidence"])
    
    # Rows
    for item in data:
        ws.append([
            item.get("rank"),
            item.get("candidate_id"),
            item.get("overall_score"),
            item.get("recommendation"),
            item.get("hiring_confidence")
        ])
        
    wb.save(filepath)

async def main():
    parser = argparse.ArgumentParser(description="Export candidate rankings to CSV, JSON, or Excel.")
    parser.add_argument("--job_id", help="Job Description ID to export rankings for. If omitted, takes the first job in DB.")
    parser.add_argument("--format", choices=["csv", "json", "excel"], default="csv", help="Target export format (csv, json, excel).")
    parser.add_argument("--output", help="Optional custom output filename. If omitted, saves under exports/ folder.")

    args = parser.parse_args()
    job_id = args.job_id
    fmt = args.format.lower()

    async with async_session_factory() as session:
        ranking_repo = RankingRepository(session)
        job_repo = JobRepository(session)

        # 1. Fetch Job
        if not job_id:
            all_jobs = await job_repo.get_all()
            if not all_jobs:
                print("Error: No jobs in database.")
                sys.exit(1)
            job_id = all_jobs[0].id

        # 2. Fetch Ranking
        ranking_record = await ranking_repo.get_ranking(job_id)
        if not ranking_record or not ranking_record.rankings:
            print(f"Error: No ranking records found for Job ID '{job_id}'. Run ranking first.")
            sys.exit(1)

        rankings_data = ranking_record.rankings
        print(f"Exporting {len(rankings_data)} candidates for Job ID: {job_id}")

        # 3. Resolve output filepath
        os.makedirs("exports", exist_ok=True)
        ext = "xlsx" if fmt == "excel" else fmt
        filepath = args.output or f"exports/ranking_{job_id}.{ext}"

        # 4. Perform Export
        if fmt == "json":
            export_data = []
            for item in rankings_data:
                export_data.append({
                    "Rank": item.get("rank"),
                    "Candidate ID": item.get("candidate_id"),
                    "Overall Score": item.get("overall_score"),
                    "Recommendation": item.get("recommendation"),
                    "Confidence": item.get("hiring_confidence")
                })
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2)
        elif fmt == "excel":
            export_to_excel(filepath, rankings_data)
        else:
            export_to_csv(filepath, rankings_data)

        print(f"Export successful. Saved to: {os.path.abspath(filepath)}")

if __name__ == "__main__":
    asyncio.run(main())
