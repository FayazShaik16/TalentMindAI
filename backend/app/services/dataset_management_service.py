import os
import time
import json
import gzip
import csv
import hashlib
import psutil
import asyncio
from typing import Any, BinaryIO
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.config.config import settings
from app.core.logging.logging import logger
from app.database.models.dataset_management import (
    Dataset, DatasetVersion, ImportHistory, EmbeddingMetadata, IndexMetadata
)
from app.database.models.candidate import (
    Candidate, Experience, Project, Education, Skill, Certification, CandidateMetadata, EngineeredFeature
)
from app.database.repositories.candidate import CandidateRepository
from app.services.pipeline import pipeline
from app.services.embedding_service import embedding_service
from app.providers.vector.faiss import FAISSProvider
from app.schemas.candidate import (
    CandidateProfile, PersonalInfo, ExperienceDetail, ProjectDetail,
    EducationDetail, SkillDetail, CertificationDetail, BehaviorSignals,
    CandidateMetadata as SchemaMetadata, EngineeredFeatures
)

def map_entity_to_profile(c: Candidate) -> CandidateProfile:
    experiences = [
        ExperienceDetail(
            company_name=e.company_name,
            job_title=e.job_title,
            start_date=e.start_date,
            end_date=e.end_date,
            description=e.description,
            is_current=e.is_current
        )
        for e in c.experiences
    ]

    projects = [
        ProjectDetail(
            name=p.name,
            description=p.description,
            technologies=p.technologies,
            domain=p.domain,
            responsibilities=p.responsibilities,
            duration_months=p.duration_months
        )
        for p in c.projects
    ]

    educations = [
        EducationDetail(
            institution=edu.institution,
            degree=edu.degree,
            field_of_study=edu.field_of_study,
            start_date=edu.start_date,
            end_date=edu.end_date
        )
        for edu in c.educations
    ]

    skills = [
        SkillDetail(
            name=s.name,
            normalized_name=s.normalized_name,
            category=s.category,
            hierarchy_path=s.hierarchy_path
        )
        for s in c.skills
    ]

    certifications = [
        CertificationDetail(
            name=cert.name,
            issuing_organization=cert.issuing_organization,
            issue_date=cert.issue_date,
            expiration_date=cert.expiration_date
        )
        for cert in c.certifications
    ]

    behavior = BehaviorSignals(
        average_tenure_years=c.features.average_tenure if c.features else 0.0,
        career_stability_score=c.features.career_stability if c.features else 0.0
    )

    meta = SchemaMetadata(
        file_hash=c.metadata_record.file_hash if c.metadata_record else None,
        version=c.metadata_record.version if c.metadata_record else 1,
        raw_payload_checksum=c.metadata_record.raw_payload_checksum if c.metadata_record else None,
        processing_duration_sec=c.metadata_record.processing_duration_sec if c.metadata_record else 0.0
    )

    feats = EngineeredFeatures(
        years_experience=c.features.years_experience if c.features else 0.0,
        distinct_companies=c.features.distinct_companies if c.features else 0,
        average_tenure=c.features.average_tenure if c.features else 0.0,
        career_stability=c.features.career_stability if c.features else 0.0,
        project_count=c.features.project_count if c.features else 0,
        certification_count=c.features.certification_count if c.features else 0,
        education_level=c.features.education_level if c.features else None,
        technology_diversity=c.features.technology_diversity if c.features else 0,
        domain_diversity=c.features.domain_diversity if c.features else 0,
        leadership_score=c.features.leadership_score if c.features else 0,
        cloud_score=c.features.cloud_score if c.features else 0,
        ai_score=c.features.ai_score if c.features else 0,
        blockchain_score=c.features.blockchain_score if c.features else 0,
        cybersecurity_score=c.features.cybersecurity_score if c.features else 0
    )

    return CandidateProfile(
        id=c.id,
        personal_info=PersonalInfo(
            first_name=c.first_name,
            last_name=c.last_name,
            email=c.email,
            phone=c.phone,
            location=c.location
        ),
        experiences=experiences,
        projects=projects,
        educations=educations,
        skills=skills,
        certifications=certifications,
        behavior_signals=behavior,
        metadata=meta,
        engineered_features=feats
    )

class DatasetProgressTracker:
    def __init__(self):
        self.stage = 0  # 1 to 10
        self.progress = 0  # 0 to 100
        self.current_record = 0
        self.total_records = 0
        self.elapsed_time = 0.0
        self.estimated_time_remaining = 0.0
        self.memory_usage_mb = 0.0
        self.status = "idle"  # idle, processing, complete, failed
        self.error_message = None
        self.dataset_name = ""
        self.start_time = 0.0
        
    def reset(self):
        self.stage = 0
        self.progress = 0
        self.current_record = 0
        self.total_records = 0
        self.elapsed_time = 0.0
        self.estimated_time_remaining = 0.0
        self.memory_usage_mb = 0.0
        self.status = "idle"
        self.error_message = None
        self.dataset_name = ""
        self.start_time = 0.0

    def update(self, stage: int, progress: int, current_record: int, total_records: int, error_message: str = None):
        self.stage = stage
        self.progress = progress
        self.current_record = current_record
        self.total_records = total_records
        if self.start_time > 0:
            self.elapsed_time = round(time.perf_counter() - self.start_time, 2)
            if progress > 0 and progress < 100:
                pct_left = (100 - progress) / progress
                self.estimated_time_remaining = round(self.elapsed_time * pct_left, 2)
            elif progress >= 100:
                self.estimated_time_remaining = 0.0
        else:
            self.elapsed_time = 0.0
            self.estimated_time_remaining = 0.0
            
        # Get memory usage
        process = psutil.Process(os.getpid())
        self.memory_usage_mb = round(process.memory_info().rss / (1024 * 1024), 2)
        if error_message:
            self.error_message = error_message
            self.status = "failed"

    def get_state(self) -> dict:
        stages_labels = {
            1: "Reading Dataset",
            2: "Parsing Candidate Records",
            3: "Validating Records",
            4: "Cleaning Data",
            5: "Building Candidate Profiles",
            6: "Generating Embeddings",
            7: "Building FAISS Vector Index",
            8: "Optimizing Search Cache",
            9: "Saving Metadata",
            10: "Dataset Ready"
        }
        return {
            "stage": self.stage,
            "stage_label": stages_labels.get(self.stage, "Idle"),
            "progress": self.progress,
            "current_record": self.current_record,
            "total_records": self.total_records,
            "elapsed_time": self.elapsed_time,
            "estimated_time_remaining": self.estimated_time_remaining,
            "memory_usage_mb": self.memory_usage_mb,
            "status": self.status,
            "error_message": self.error_message,
            "dataset_name": self.dataset_name
        }

progress_tracker = DatasetProgressTracker()

class DatasetManagementService:
    def calculate_file_hash(self, file_path: str) -> str:
        hasher = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def validate_file(self, file_path: str) -> tuple[bool, str | None]:
        # Validate file size
        max_size = 600 * 1024 * 1024  # 600MB
        if os.path.getsize(file_path) > max_size:
            return False, "File exceeds maximum size of 600MB."

        # Validate file format
        ext = os.path.splitext(file_path)[1].lower()
        if file_path.endswith(".jsonl.gz"):
            ext = ".jsonl.gz"
        if ext not in [".jsonl", ".jsonl.gz", ".csv"]:
            return False, "Unsupported file format. Supported formats: .jsonl, .jsonl.gz, .csv"

        # Validate content structure (try reading the first line/record)
        try:
            if ext == ".jsonl.gz":
                with gzip.open(file_path, "rt", encoding="utf-8") as f:
                    first_line = f.readline()
                    if not first_line:
                        return False, "Corrupted GZIP or empty file."
                    json.loads(first_line)
            elif ext == ".jsonl":
                with open(file_path, "r", encoding="utf-8") as f:
                    first_line = f.readline()
                    if not first_line:
                        return False, "Empty JSONL file."
                    json.loads(first_line)
            elif ext == ".csv":
                with open(file_path, "r", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    header = next(reader, None)
                    if not header:
                        return False, "Empty CSV file."
                    # Check expected columns
                    required = ["id", "first_name", "last_name"]
                    missing = [r for r in required if r not in header]
                    if missing:
                        return False, f"CSV missing required columns: {', '.join(missing)}"
        except json.JSONDecodeError:
            return False, "Malformed JSONL syntax on first line."
        except Exception as e:
            return False, f"Validation failed: {str(e)}"

        return True, None

    async def import_pipeline(self, file_path: str, dataset_name: str):
        from app.database.session import get_db_session
        global progress_tracker
        progress_tracker.reset()
        progress_tracker.start_time = time.perf_counter()
        progress_tracker.dataset_name = dataset_name
        progress_tracker.status = "processing"
        async for db in get_db_session():
            await self._run_import(file_path, dataset_name, db)

    async def _run_import(self, file_path: str, dataset_name: str, db: AsyncSession):
        try:
            # Stage 1: Reading Dataset
            progress_tracker.update(1, 10, 0, 0)
            await asyncio.sleep(0.5)

            # Calculate file hash and size
            file_hash = self.calculate_file_hash(file_path)
            file_size = os.path.getsize(file_path)

            # Stage 2: Parsing Candidate Records
            progress_tracker.update(2, 20, 0, 0)
            records = []
            ext = os.path.splitext(file_path)[1].lower()
            if file_path.endswith(".jsonl.gz"):
                ext = ".jsonl.gz"

            if ext == ".jsonl.gz":
                with gzip.open(file_path, "rt", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            records.append(json.loads(line))
            elif ext == ".jsonl":
                with open(file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            records.append(json.loads(line))
            elif ext == ".csv":
                with open(file_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    records = [dict(row) for row in reader]

            total_records = len(records)
            if total_records == 0:
                raise ValueError("Dataset contains no records.")

            # Stage 3: Validating Records
            progress_tracker.update(3, 30, 0, total_records)
            valid_records = []
            failed_count = 0
            for idx, r in enumerate(records):
                is_valid, _ = pipeline.validate_record(r)
                if is_valid:
                    valid_records.append(pipeline.normalize_record(r))
                else:
                    failed_count += 1
                if idx % 100 == 0:
                    progress_tracker.update(3, 30 + int((idx / total_records) * 10), idx, total_records)
                    await asyncio.sleep(0.01)

            # Stage 4: Cleaning Data & Deduplicating
            progress_tracker.update(4, 40, len(valid_records), total_records)
            unique_records = []
            seen_ids = set()
            for r in valid_records:
                c_id = str(r["id"]).strip()
                if c_id not in seen_ids:
                    seen_ids.add(c_id)
                    unique_records.append(r)
            
            # Stage 5: Building Candidate Profiles
            progress_tracker.update(5, 50, 0, len(unique_records))
            success_count = 0
            
            # Create primary dataset record
            dataset = Dataset(
                name=dataset_name,
                file_path=file_path,
                file_size=file_size,
                status="processing",
                total_candidates=len(unique_records)
            )
            db.add(dataset)
            await db.flush()

            version = DatasetVersion(
                dataset_id=dataset.id,
                version=1,
                file_hash=file_hash,
                status="processing"
            )
            db.add(version)
            await db.flush()

            repo = CandidateRepository(db)
            
            for idx, raw_record in enumerate(unique_records):
                # Standard cleaning of subfields
                experiences_raw = raw_record.get("experiences", [])
                if isinstance(experiences_raw, str):
                    experiences_raw = json.loads(experiences_raw)
                from app.schemas.candidate import (
                    CandidateProfile, PersonalInfo, ExperienceDetail, ProjectDetail,
                    EducationDetail, SkillDetail, CertificationDetail, BehaviorSignals,
                    CandidateMetadata as SchemaMetadata
                )
                from app.services.extractor import career_extractor
                from app.services.feature_engineer import feature_engineer
                from app.services.normalizer import skill_normalizer
                from app.utils.caching import disk_cache

                experiences = [ExperienceDetail(**exp) for exp in experiences_raw]

                projects_raw = raw_record.get("projects", [])
                if isinstance(projects_raw, str):
                    projects_raw = json.loads(projects_raw)
                projects = [ProjectDetail(**proj) for proj in projects_raw]

                educations_raw = raw_record.get("educations", [])
                if isinstance(educations_raw, str):
                    educations_raw = json.loads(educations_raw)
                educations = [EducationDetail(**edu) for edu in educations_raw]

                certifications_raw = raw_record.get("certifications", [])
                if isinstance(certifications_raw, str):
                    certifications_raw = json.loads(certifications_raw)
                certifications = [CertificationDetail(**cert) for cert in certifications_raw]

                skills_raw = raw_record.get("skills", [])
                if isinstance(skills_raw, str):
                    skills_raw = json.loads(skills_raw)
                skills = []
                for s in skills_raw:
                    s_name = s.get("name") if isinstance(s, dict) else str(s)
                    cache_key = f"skill_norm_{s_name.lower().strip()}"
                    cached_skill = disk_cache.get(cache_key)
                    if cached_skill:
                        skills.append(SkillDetail(**cached_skill))
                    else:
                        norm_res = skill_normalizer.normalize(s_name)
                        disk_cache.set(cache_key, norm_res)
                        skills.append(SkillDetail(**norm_res))

                timeline = career_extractor.extract_timeline_metrics(experiences)
                behavior = BehaviorSignals(
                    average_tenure_years=timeline["average_tenure"],
                    career_stability_score=timeline["career_stability"]
                )

                features = feature_engineer.engineer_features(
                    years_exp=timeline["years_experience"],
                    distinct_comps=timeline["distinct_companies"],
                    avg_tenure=timeline["average_tenure"],
                    stability=timeline["career_stability"],
                    experiences=experiences,
                    projects=projects,
                    educations=educations,
                    skills=skills,
                    certifications=certifications
                )

                payload_hash = pipeline._get_payload_hash(raw_record)
                profile = CandidateProfile(
                    id=str(raw_record["id"]).strip(),
                    personal_info=PersonalInfo(
                        first_name=raw_record["first_name"].strip(),
                        last_name=raw_record["last_name"].strip(),
                        email=raw_record.get("email"),
                        phone=raw_record.get("phone"),
                        location=raw_record.get("location"),
                    ),
                    experiences=experiences,
                    projects=projects,
                    educations=educations,
                    skills=skills,
                    certifications=certifications,
                    behavior_signals=behavior,
                    metadata=SchemaMetadata(
                        file_hash=payload_hash,
                        version=1,
                        raw_payload_checksum=payload_hash,
                        processing_duration_sec=0.0
                    ),
                    engineered_features=features
                )

                await repo.upsert_candidate_profile(profile)
                success_count += 1
                if idx % 2000 == 0:
                    progress_tracker.update(5, 50 + int((idx / len(unique_records)) * 10), idx, len(unique_records))
                    await db.commit()
                    await asyncio.sleep(0.001)

            await db.commit()

            # Stage 6: Generating Embeddings
            progress_tracker.update(6, 60, 0, len(unique_records))
            
            if len(unique_records) <= 1000:
                candidates = await repo.get_all()
                emb_start = time.perf_counter()
                for idx, cand in enumerate(candidates):
                    profile = map_entity_to_profile(cand)
                    # This checks persistent SQLite cache, so it is fast and respects previous builds!
                    await embedding_service.get_candidate_embeddings(profile)
                    if idx % 50 == 0:
                        progress_tracker.update(6, 60 + int((idx / len(candidates)) * 10), idx, len(candidates))
                        await asyncio.sleep(0.01)

                emb_duration = time.perf_counter() - emb_start
                emb_count = len(candidates)
            else:
                emb_duration = 0.0
                emb_count = 0

            emb_metadata = EmbeddingMetadata(
                dataset_id=dataset.id,
                version_id=version.id,
                total_embeddings=emb_count,
                status="ready" if emb_count > 0 else "deferred",
                duration_sec=emb_duration
            )
            db.add(emb_metadata)
            await db.commit()

            # Stage 7: Building FAISS Vector Index
            progress_tracker.update(7, 70, 0, len(unique_records))
            
            if len(unique_records) <= 1000:
                provider = FAISSProvider()
                # Index candidates in FAISS
                from app.api.v1.routers.semantic import index_candidate_profile
                idx_start = time.perf_counter()
                for idx, cand in enumerate(candidates):
                    await index_candidate_profile(cand, db, provider)
                    if idx % 50 == 0:
                        progress_tracker.update(7, 70 + int((idx / len(candidates)) * 10), idx, len(candidates))
                        await asyncio.sleep(0.01)

                idx_duration = time.perf_counter() - idx_start
                
                # Save FAISS collection statistics
                faiss_stats = await provider.get_statistics("summary")
                ntotal = faiss_stats.get("ntotal", 0)
                dimension = faiss_stats.get("dimension", 0)
                metric_type = faiss_stats.get("metric_type", "")
                index_type = faiss_stats.get("index_type", "")
                status_val = "ready"
            else:
                ntotal = 0
                dimension = 0
                metric_type = ""
                index_type = ""
                status_val = "deferred"

            index_meta = IndexMetadata(
                dataset_id=dataset.id,
                version_id=version.id,
                ntotal=ntotal,
                dimension=dimension,
                metric_type=metric_type,
                index_type=index_type,
                status=status_val
            )
            db.add(index_meta)
            await db.commit()

            # Stage 8: Optimizing Search Cache
            progress_tracker.update(8, 80, len(unique_records), len(unique_records))
            await asyncio.sleep(0.5)

            # Stage 9: Saving Metadata
            progress_tracker.update(9, 90, len(unique_records), len(unique_records))
            
            duration = time.perf_counter() - progress_tracker.start_time
            import_history = ImportHistory(
                dataset_id=dataset.id,
                version_id=version.id,
                filename=os.path.basename(file_path),
                file_size=file_size,
                total_records=total_records,
                successful_records=success_count,
                failed_records=failed_count + (total_records - success_count - failed_count),
                duration_sec=duration,
                status="success"
            )
            db.add(import_history)
            
            # Update dataset active status
            dataset.status = "ready"
            dataset.embeddings_generated = emb_count
            version.status = "ready"
            await db.commit()

            # Stage 10: Dataset Ready
            progress_tracker.update(10, 100, len(unique_records), len(unique_records))
            progress_tracker.status = "complete"

        except Exception as e:
            logger.error("dataset_import_failed", error=str(e))
            progress_tracker.status = "failed"
            progress_tracker.error_message = str(e)
            
            # Log failure in history
            try:
                import_history = ImportHistory(
                    dataset_id=dataset.id if 'dataset' in locals() else "unknown",
                    version_id=version.id if 'version' in locals() else None,
                    filename=os.path.basename(file_path),
                    file_size=os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                    total_records=total_records if 'total_records' in locals() else 0,
                    successful_records=success_count if 'success_count' in locals() else 0,
                    failed_records=total_records - success_count if ('total_records' in locals() and 'success_count' in locals()) else 0,
                    duration_sec=time.perf_counter() - progress_tracker.start_time,
                    status="failed",
                    error_message=str(e)
                )
                db.add(import_history)
                if 'dataset' in locals():
                    dataset.status = "failed"
                await db.commit()
            except Exception as inner_e:
                logger.error("failed_to_log_import_failure", error=str(inner_e))

    async def reset_dataset(self, db: AsyncSession):
        from app.database.models.candidate_evidence import CandidateEvidence
        from app.database.models.candidate_intelligence import CandidateIntelligence
        from app.database.models.explanation import JobCandidateExplanation
        from app.database.models.job import JobDescription
        from app.database.models.ranking import JobCandidateRanking
        from app.database.models.workspace import RecruiterWorkspace, JobSession, RecruiterActivity

        # Clear all candidates, experiences, projects, educations, skills, certifications, metadata, features
        await db.execute(delete(Experience))
        await db.execute(delete(Project))
        await db.execute(delete(Education))
        await db.execute(delete(Skill))
        await db.execute(delete(Certification))
        await db.execute(delete(CandidateMetadata))
        await db.execute(delete(EngineeredFeature))
        await db.execute(delete(Candidate))

        # Clear intelligence, evidence and explanation tables
        await db.execute(delete(CandidateEvidence))
        await db.execute(delete(CandidateIntelligence))
        await db.execute(delete(JobCandidateExplanation))

        # Clear job and session models
        await db.execute(delete(JobCandidateRanking))
        await db.execute(delete(JobSession))
        await db.execute(delete(RecruiterWorkspace))
        await db.execute(delete(RecruiterActivity))
        await db.execute(delete(JobDescription))

        # Clear dataset management tables
        await db.execute(delete(ImportHistory))
        await db.execute(delete(EmbeddingMetadata))
        await db.execute(delete(IndexMetadata))
        await db.execute(delete(DatasetVersion))
        await db.execute(delete(Dataset))
        await db.commit()

        # Clear FAISS index
        provider = FAISSProvider()
        for col in ["summary", "career", "projects", "skills", "education"]:
            await provider.clear_collection(col)

        # Clear embedding cache
        embedding_service.clear_cache()
        
        progress_tracker.reset()

dataset_mgmt_service = DatasetManagementService()
