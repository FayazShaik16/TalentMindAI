import io
import json
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from app.database.models.candidate import (
    Candidate, Experience, Skill, EngineeredFeature,
    Project, Education, Certification, CandidateMetadata
)
from app.database.repositories.candidate import CandidateRepository
from app.schemas.candidate import CandidateProfile, PersonalInfo, SkillDetail

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


@pytest.mark.asyncio
async def test_dataset_api_workflow(client: AsyncClient, db_session: AsyncSession):
    """
    Test uploading a dataset, processing it, checking status, fetching statistics,
    and retrieving specific candidate sub-resources.
    """
    await clear_db(db_session)

    # 1. Check status initially
    status_response = await client.get("/api/v1/dataset/status")
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["success"] is True
    assert status_data["data"]["status"] in ["ready", "complete"]

    # 2. Upload dataset file
    csv_content = (
        "id,first_name,last_name,email,phone,location,experiences,projects,educations,skills,certifications\n"
        "api_cand_01,Jane,Doe,jane@example.com,+1234,Austin,[],[],[],[],[]"
    )
    files = {"file": ("dataset.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    upload_response = await client.post("/api/v1/dataset/upload", files=files)
    assert upload_response.status_code == 200
    upload_data = upload_response.json()
    assert upload_data["success"] is True
    assert "filepath" in upload_data["data"]

    uploaded_filepath = upload_data["data"]["filepath"]

    # 3. Process dataset file
    process_response = await client.post("/api/v1/dataset/process", params={"filepath": uploaded_filepath})
    assert process_response.status_code == 200
    process_data = process_response.json()
    assert process_data["success"] is True
    assert process_data["data"]["total_records"] == 1
    assert process_data["data"]["successful_inserts"] == 1

    # 4. Check status again to see it's complete
    status_response_after = await client.get("/api/v1/dataset/status")
    status_data_after = status_response_after.json()
    assert status_data_after["data"]["status"] == "complete"
    assert status_data_after["data"]["last_uploaded_file"] == uploaded_filepath

    # 5. Fetch statistics
    stats_response = await client.get("/api/v1/dataset/statistics")
    assert stats_response.status_code == 200
    stats_data = stats_response.json()
    assert stats_data["success"] is True
    assert stats_data["data"]["total_candidates"] >= 1

    # 6. Fetch candidate basic info
    cand_response = await client.get("/api/v1/dataset/candidate/api_cand_01")
    assert cand_response.status_code == 200
    cand_data = cand_response.json()
    assert cand_data["success"] is True
    assert cand_data["data"]["first_name"] == "Jane"
    assert cand_data["data"]["last_name"] == "Doe"

    # 7. Fetch candidate full profile
    profile_response = await client.get("/api/v1/dataset/candidate/api_cand_01/profile")
    assert profile_response.status_code == 200
    profile_data = profile_response.json()
    assert profile_data["success"] is True
    assert profile_data["data"]["id"] == "api_cand_01"
    assert profile_data["data"]["personal_info"]["first_name"] == "Jane"

    # 8. Fetch candidate career/experiences
    career_response = await client.get("/api/v1/dataset/candidate/api_cand_01/career")
    assert career_response.status_code == 200
    career_data = career_response.json()
    assert career_data["success"] is True
    assert isinstance(career_data["data"], list)

    # 9. Fetch candidate projects
    projects_response = await client.get("/api/v1/dataset/candidate/api_cand_01/projects")
    assert projects_response.status_code == 200
    projects_data = projects_response.json()
    assert projects_data["success"] is True
    assert isinstance(projects_data["data"], list)

    # 10. Fetch candidate skills
    skills_response = await client.get("/api/v1/dataset/candidate/api_cand_01/skills")
    assert skills_response.status_code == 200
    skills_data = skills_response.json()
    assert skills_data["success"] is True
    assert isinstance(skills_data["data"], list)

@pytest.mark.asyncio
async def test_dataset_api_candidate_not_found(client: AsyncClient):
    """
    Test retrieving a non-existent candidate ID returns a 404 error.
    """
    res1 = await client.get("/api/v1/dataset/candidate/non_existent_id")
    assert res1.status_code == 404
    assert res1.json()["error"]["message"] == "Candidate not found"

    res2 = await client.get("/api/v1/dataset/candidate/non_existent_id/profile")
    assert res2.status_code == 404

    res3 = await client.get("/api/v1/dataset/candidate/non_existent_id/career")
    assert res3.status_code == 404

    res4 = await client.get("/api/v1/dataset/candidate/non_existent_id/projects")
    assert res4.status_code == 404

    res5 = await client.get("/api/v1/dataset/candidate/non_existent_id/skills")
    assert res5.status_code == 404

@pytest.mark.asyncio
async def test_dataset_root_endpoints(client: AsyncClient, db_session: AsyncSession):
    """
    Test root aliases for dataset uploads and candidate profiles.
    """
    await clear_db(db_session)
    
    # Test Root Upload
    csv_content = (
        "id,first_name,last_name,email,phone,location,experiences,projects,educations,skills,certifications\n"
        "root_cand_01,John,Smith,john@example.com,+5678,London,[],[],[],[],[]"
    )
    files = {"file": ("root_dataset.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    upload_response = await client.post("/dataset/upload", files=files)
    assert upload_response.status_code == 200
    upload_data = upload_response.json()
    assert upload_data["success"] is True
    assert "filepath" in upload_data["data"]
    
    uploaded_filepath = upload_data["data"]["filepath"]
    
    # Process dataset file (via api version endpoint)
    process_response = await client.post("/api/v1/dataset/process", params={"filepath": uploaded_filepath})
    assert process_response.status_code == 200
    
    # Test Root Candidate details fetch
    cand_response = await client.get("/candidate/root_cand_01")
    assert cand_response.status_code == 200
    cand_data = cand_response.json()
    assert cand_data["success"] is True
    assert cand_data["data"]["first_name"] == "John"
    
    # Test Root Candidate Profile fetch
    profile_response = await client.get("/candidate/root_cand_01/profile")
    assert profile_response.status_code == 200
    profile_data = profile_response.json()
    assert profile_data["success"] is True
    assert profile_data["data"]["id"] == "root_cand_01"
    
    # Test Candidate Not Found Root
    res_err1 = await client.get("/candidate/non_existent_root")
    assert res_err1.status_code == 404
    
    res_err2 = await client.get("/candidate/non_existent_root/profile")
    assert res_err2.status_code == 404

