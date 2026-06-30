import os
import json
import pytest
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.pipeline import pipeline
from app.database.models.candidate import (
    Candidate, Experience, Skill, EngineeredFeature,
    Project, Education, Certification, CandidateMetadata
)
from app.database.repositories.candidate import CandidateRepository

async def clear_db(db_session: AsyncSession):
    await db_session.execute(delete(CandidateMetadata))
    await db_session.execute(delete(EngineeredFeature))
    await db_session.execute(delete(Experience))
    await db_session.execute(delete(Project))
    await db_session.execute(delete(Education))
    await db_session.execute(delete(Skill))
    await db_session.execute(delete(Certification))
    await db_session.execute(delete(Candidate))
    await db_session.commit()


# Create helper functions to write mock files
def create_mock_csv(path: str, data: list[dict]):
    import csv
    if not data:
        return
    keys = data[0].keys()
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for row in data:
            writer.writerow(row)

def create_mock_json(path: str, data: list[dict]):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)

def create_mock_jsonl(path: str, data: list[dict]):
    with open(path, "w", encoding="utf-8") as f:
        for row in data:
            f.write(json.dumps(row) + "\n")

def create_mock_xlsx(path: str, data: list[dict]):
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    if not data:
        wb.save(path)
        return
    headers = list(data[0].keys())
    ws.append(headers)
    for row in data:
        ws.append([row.get(h) for h in headers])
    wb.save(path)

def create_mock_parquet(path: str, data: list[dict]):
    import pyarrow as pa
    import pyarrow.parquet as pq
    table = pa.Table.from_pylist(data)
    pq.write_table(table, path)


@pytest.fixture
def mock_candidates():
    return [
        {
            "id": "cand_01",
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
            "phone": "+11111",
            "location": "San Francisco",
            "experiences": json.dumps([
                {
                    "company_name": "Tech Corp",
                    "job_title": "AI Engineer",
                    "start_date": "2020-01-01",
                    "end_date": "2022-01-01",
                    "description": "Working on machine learning models",
                    "is_current": False
                }
            ]),
            "projects": json.dumps([
                {
                    "name": "Translation Service",
                    "description": "AWS and PyTorch translator",
                    "technologies": ["AWS", "PyTorch"],
                    "domain": "NLP",
                    "responsibilities": ["Model training"]
                }
            ]),
            "educations": json.dumps([
                {
                    "institution": "Stanford",
                    "degree": "M.S.",
                    "field_of_study": "CS",
                    "start_date": "2018-09-01",
                    "end_date": "2020-06-01"
                }
            ]),
            "skills": json.dumps(["Python", "AWS", "Machine Learning"]),
            "certifications": json.dumps([
                {
                    "name": "AWS Solutions Architect",
                    "issuing_organization": "Amazon"
                }
            ])
        },
        {
            "id": "cand_02",
            "first_name": "Bob",
            "last_name": "Jones",
            "email": "bob@example.com",
            "phone": "+22222",
            "location": "Boston",
            "experiences": json.dumps([
                {
                    "company_name": "Retailer Inc",
                    "job_title": "Java Developer",
                    "start_date": "2015-05-01",
                    "end_date": "2019-05-01",
                    "description": "Backend services",
                    "is_current": False
                }
            ]),
            "projects": json.dumps([]),
            "educations": json.dumps([]),
            "skills": json.dumps(["Java", "Spring"]),
            "certifications": json.dumps([])
        }
    ]

@pytest.mark.asyncio
async def test_parse_all_file_formats(tmp_path, mock_candidates):
    """
    Test that CSV, JSON, JSONL, XLSX, Parquet parsing outputs identical records.
    """
    csv_file = os.path.join(tmp_path, "candidates.csv")
    json_file = os.path.join(tmp_path, "candidates.json")
    jsonl_file = os.path.join(tmp_path, "candidates.jsonl")
    xlsx_file = os.path.join(tmp_path, "candidates.xlsx")
    parquet_file = os.path.join(tmp_path, "candidates.parquet")

    create_mock_csv(csv_file, mock_candidates)
    create_mock_json(json_file, mock_candidates)
    create_mock_jsonl(jsonl_file, mock_candidates)
    create_mock_xlsx(xlsx_file, mock_candidates)
    create_mock_parquet(parquet_file, mock_candidates)

    records_csv = pipeline.parse_file(csv_file)
    records_json = pipeline.parse_file(json_file)
    records_jsonl = pipeline.parse_file(jsonl_file)
    records_xlsx = pipeline.parse_file(xlsx_file)
    records_parquet = pipeline.parse_file(parquet_file)

    # Validate parsing lengths
    assert len(records_csv) == 2
    assert len(records_json) == 2
    assert len(records_jsonl) == 2
    assert len(records_xlsx) == 2
    assert len(records_parquet) == 2

    # Verify key field matches across JSON and CSV
    assert str(records_csv[0]["id"]) == "cand_01"
    assert str(records_json[0]["id"]) == "cand_01"
    assert str(records_xlsx[0]["id"]) == "cand_01"
    assert str(records_parquet[0]["id"]) == "cand_01"

@pytest.mark.asyncio
async def test_full_ingestion_pipeline(tmp_path, mock_candidates, db_session: AsyncSession):
    """
    Test loading, validating, cleaning, saving, and checking analytics reports.
    """
    json_file = os.path.join(tmp_path, "candidates.json")
    create_mock_json(json_file, mock_candidates)

    # Clear database candidates first
    await clear_db(db_session)
    
    # Process
    report = await pipeline.process_dataset(json_file, db_session)
    assert report["total_records"] == 2
    assert report["successful_inserts"] == 2
    assert report["validation_failures"] == 0
    assert report["duplicate_skips"] == 0

    # Verify db items
    repo = CandidateRepository(db_session)
    c1 = await repo.get_candidate_profile("cand_01")
    assert c1 is not None
    assert c1.first_name == "Alice"
    assert len(c1.experiences) == 1
    assert c1.experiences[0].company_name == "Tech Corp"
    assert len(c1.skills) == 3

    # Check skill category mappings
    skill_names = [s.normalized_name for s in c1.skills]
    assert "Python" in skill_names
    assert "Machine Learning" in skill_names

    # Check features engineered
    assert c1.features is not None
    assert c1.features.education_level == "Master"
    assert c1.features.years_experience == 2.0
    assert c1.features.ai_score >= 1  # Alice has "AI Engineer" and "Machine Learning"

    # Check statistics API
    stats = await repo.get_dataset_analytics()
    assert stats["total_candidates"] == 2
    assert stats["average_experience_years"] == 3.0  # (2.0 + 4.0) / 2

@pytest.mark.asyncio
async def test_incremental_processing_and_failures(tmp_path, mock_candidates, db_session: AsyncSession):
    """
    Test that identical records are skipped via file hash check, and validation failures continue execution.
    """
    # Clear database candidates first
    await clear_db(db_session)

    # 1. Ingest initial list
    json_file = os.path.join(tmp_path, "candidates.json")
    create_mock_json(json_file, mock_candidates)
    await pipeline.process_dataset(json_file, db_session)

    # 2. Ingest again with same list -> Should skip both candidates as incremental skips
    report2 = await pipeline.process_dataset(json_file, db_session)
    assert report2["successful_inserts"] == 0
    assert report2["incremental_skips"] == 2

    # 3. Add one invalid candidate, one updated candidate, and one new candidate
    modified_candidates = [
        # Invalid candidate (no ID)
        {
            "id": "",
            "first_name": "No ID User",
            "last_name": "No ID",
            "email": "noid@example.com"
        },
        # Updated candidate (modified experience description)
        {
            "id": "cand_01",
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
            "phone": "+11111",
            "location": "San Francisco",
            "experiences": json.dumps([
                {
                    "company_name": "Tech Corp",
                    "job_title": "Principal AI Architect",  # Promotion & title change
                    "start_date": "2020-01-01",
                    "end_date": "2023-01-01",               # Tenure change
                    "description": "Architecting large scale ML and LLM pipelines",
                    "is_current": False
                }
            ]),
            "projects": json.dumps([]),
            "educations": json.dumps([]),
            "skills": json.dumps(["Python", "LLM", "AWS"]),
            "certifications": json.dumps([])
        },
        # New candidate
        {
            "id": "cand_03",
            "first_name": "Charlie",
            "last_name": "Brown",
            "email": "charlie@example.com",
            "phone": "+33333",
            "location": "Seattle",
            "experiences": json.dumps([]),
            "projects": json.dumps([]),
            "educations": json.dumps([]),
            "skills": json.dumps([]),
            "certifications": json.dumps([])
        }
    ]

    json_file2 = os.path.join(tmp_path, "candidates_mod.json")
    create_mock_json(json_file2, modified_candidates)

    # Process modified list
    report3 = await pipeline.process_dataset(json_file2, db_session)
    # total records = 3
    # successful inserts = 2 (cand_01 updated, cand_03 created)
    # validation failures = 1 (no ID)
    # incremental skips = 0
    assert report3["total_records"] == 3
    assert report3["successful_inserts"] == 2
    assert report3["validation_failures"] == 1
    assert report3["incremental_skips"] == 0

    # Query Alice again to check the updates
    repo = CandidateRepository(db_session)
    c1_updated = await repo.get_candidate_profile("cand_01")
    assert c1_updated.experiences[0].job_title == "Principal AI Architect"
    assert c1_updated.features.years_experience == 3.0
    assert c1_updated.features.leadership_score > 0  # "Principal"
