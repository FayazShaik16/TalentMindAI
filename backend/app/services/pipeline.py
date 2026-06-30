import os
import csv
import json
import time
import hashlib
import psutil
from typing import Any, Generator
from sqlalchemy.ext.asyncio import AsyncSession

# Dynamic imports for formats
import openpyxl
import pyarrow.parquet as pq

from app.core.config.config import settings
from app.core.logging.logging import logger
from app.schemas.candidate import (
    CandidateProfile, PersonalInfo, ExperienceDetail, ProjectDetail,
    EducationDetail, SkillDetail, CertificationDetail, BehaviorSignals,
    CandidateMetadata
)
from app.database.repositories.candidate import CandidateRepository
from app.services.normalizer import skill_normalizer
from app.services.extractor import career_extractor
from app.services.feature_engineer import feature_engineer
from app.utils.caching import disk_cache

class DatasetPipeline:
    EXPECTED_COLUMNS = ["id", "first_name", "last_name", "email", "phone", "location"]

    def _get_payload_hash(self, payload: dict) -> str:
        """
        Generate a unique hash for a candidate payload dictionary to support incremental updates.
        """
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.md5(serialized.encode("utf-8")).hexdigest()

    def detect_schema(self, first_row: dict) -> dict:
        """
        Detects dataset schema, columns, type shapes, and generates validation report.
        """
        keys = list(first_row.keys())
        missing = [col for col in self.EXPECTED_COLUMNS if col not in keys]
        
        return {
            "columns_found": keys,
            "missing_required_columns": missing,
            "is_valid": len(missing) == 0,
        }

    def parse_file(self, file_path: str) -> list[dict[str, Any]]:
        """
        Parses different file formats (CSV, JSON, JSONL, Excel, Parquet) into Python dictionaries.
        """
        ext = os.path.splitext(file_path)[1].lower()
        records = []

        if ext == ".csv":
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                records = [dict(row) for row in reader]

        elif ext == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                records = data if isinstance(data, list) else [data]

        elif ext == ".jsonl":
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        records.append(json.loads(line))

        elif ext == ".xlsx":
            wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
            sheet = wb.active
            rows = list(sheet.iter_rows(values_only=True))
            if rows:
                headers = [str(h) for h in rows[0]]
                for r in rows[1:]:
                    records.append(dict(zip(headers, r)))

        elif ext == ".parquet":
            table = pq.read_table(file_path)
            records = table.to_pylist()

        else:
            raise ValueError(f"Unsupported file format: {ext}")

        return records

    def normalize_record(self, r: dict) -> dict:
        """
        Standardizes schema variations in the uploaded dataset.
        Maps fields like 'candidate_id' -> 'id', 'anonymized_name' -> first_name/last_name, etc.
        """
        normalized = dict(r)
        
        # 1. Map ID
        if "candidate_id" in r and not r.get("id"):
            normalized["id"] = r["candidate_id"]
            
        # 2. Map profile sub-dictionary
        profile = r.get("profile")
        if isinstance(profile, dict):
            # Map first_name & last_name from anonymized_name
            name = profile.get("anonymized_name") or profile.get("name")
            if name and (not r.get("first_name") or not r.get("last_name")):
                parts = name.strip().split(maxsplit=1)
                normalized["first_name"] = parts[0]
                normalized["last_name"] = parts[1] if len(parts) > 1 else ""
                
            # Map location, email, phone if missing at root
            for field in ["location", "email", "phone"]:
                if field in profile and not r.get(field):
                    normalized[field] = profile[field]
                    
        # 3. Map experiences from career_history
        if "career_history" in r and not r.get("experiences"):
            experiences = []
            for exp in r["career_history"]:
                if isinstance(exp, dict):
                    new_exp = dict(exp)
                    if "company" in exp and "company_name" not in exp:
                        new_exp["company_name"] = exp["company"]
                    if "title" in exp and "job_title" not in exp:
                        new_exp["job_title"] = exp["title"]
                    experiences.append(new_exp)
            normalized["experiences"] = experiences
            
        # 4. Map educations from education
        if "education" in r and not r.get("educations"):
            normalized["educations"] = r["education"]
            
        # 5. Map certifications
        if "certifications" in r and not r.get("certifications"):
            normalized["certifications"] = r["certifications"]
            
        # 6. Map skills (list of strings or list of dicts with name key)
        if "skills" in r:
            skills_raw = r["skills"]
            if isinstance(skills_raw, list):
                skills_list = []
                for s in skills_raw:
                    if isinstance(s, dict) and "name" in s:
                        skills_list.append(s["name"])
                    elif isinstance(s, str):
                        skills_list.append(s)
                normalized["skills"] = skills_list
                
        return normalized

    def validate_record(self, r: dict) -> tuple[bool, str | None]:
        """
        Validates core record parameters (ID present, valid name format).
        """
        cand_id = r.get("id") or r.get("candidate_id")
        if not cand_id:
            return False, "Missing candidate ID"
            
        first_name = r.get("first_name")
        last_name = r.get("last_name")
        profile = r.get("profile")
        
        if not first_name or not last_name:
            if isinstance(profile, dict) and (profile.get("anonymized_name") or profile.get("name")):
                pass
            else:
                return False, "Missing first_name or last_name"
                
        return True, None

    async def process_dataset(self, file_path: str, db: AsyncSession) -> dict:
        """
        Executes the full preprocessing pipeline: parses, validates, cleans, normalizes,
        engineers features, and persists to the database with incremental cache checks.
        """
        start_time = time.perf_counter()
        process = psutil.Process(os.getpid())
        start_mem = process.memory_info().rss

        logger.info("processing_dataset_start", file_path=file_path)
        records = self.parse_file(file_path)
        total_rows = len(records)

        if total_rows == 0:
            return {"status": "empty_dataset", "processed": 0}

        # Run schema validation on first row (standardize check)
        first_row_normalized = self.normalize_record(records[0])
        schema_report = self.detect_schema(first_row_normalized)
        if not schema_report["is_valid"]:
            logger.warning("invalid_dataset_schema", missing=schema_report["missing_required_columns"])

        repo = CandidateRepository(db)

        # Counter metrics
        success_count = 0
        validation_failures = 0
        duplicate_skips = 0
        incremental_skips = 0
        processed_ids = set()

        for idx, raw_record in enumerate(records):
            # 1. Basic validation check
            is_valid, err_msg = self.validate_record(raw_record)
            if not is_valid:
                validation_failures += 1
                logger.warning("record_validation_failed", index=idx, error=err_msg)
                continue

            raw_record = self.normalize_record(raw_record)
            c_id = str(raw_record["id"]).strip()

            # 2. De-duplicate inside the same batch
            if c_id in processed_ids:
                duplicate_skips += 1
                continue
            processed_ids.add(c_id)

            # 3. Incremental checking via MD5 hash comparison
            payload_hash = self._get_payload_hash(raw_record)
            existing_cand = await repo.get_candidate_profile(c_id)

            if existing_cand and existing_cand.metadata_record:
                if existing_cand.metadata_record.file_hash == payload_hash:
                    incremental_skips += 1
                    continue

            # Measure record execution time
            rec_start_time = time.perf_counter()

            # 4. Clean & Parse related lists
            # Supporting both standard Python structures and raw JSON-string parameters
            experiences_raw = raw_record.get("experiences", [])
            if isinstance(experiences_raw, str):
                experiences_raw = json.loads(experiences_raw)
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

            # Parse skills and run skill normalizer
            skills_raw = raw_record.get("skills", [])
            if isinstance(skills_raw, str):
                skills_raw = json.loads(skills_raw)
            skills = []
            for s in skills_raw:
                s_name = s.get("name") if isinstance(s, dict) else str(s)
                # Check normalizer cache first
                cache_key = f"skill_norm_{s_name.lower().strip()}"
                cached_skill = disk_cache.get(cache_key)
                if cached_skill:
                    skills.append(SkillDetail(**cached_skill))
                else:
                    norm_res = skill_normalizer.normalize(s_name)
                    disk_cache.set(cache_key, norm_res)
                    skills.append(SkillDetail(**norm_res))

            # 5. Extraction of timelines and signals
            timeline = career_extractor.extract_timeline_metrics(experiences)
            behavior = BehaviorSignals(
                average_tenure_years=timeline["average_tenure"],
                career_stability_score=timeline["career_stability"]
            )

            # 6. Feature Engineering
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

            # Duration tracking
            rec_duration = time.perf_counter() - rec_start_time

            # 7. Map Pydantic Candidate Profile
            profile = CandidateProfile(
                id=c_id,
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
                metadata=CandidateMetadata(
                    file_hash=payload_hash,
                    version=1,
                    raw_payload_checksum=payload_hash,
                    processing_duration_sec=rec_duration
                ),
                engineered_features=features
            )

            # 8. Upsert in DB
            await repo.upsert_candidate_profile(profile)
            success_count += 1

            # Commit periodically in batches
            if success_count % settings.PROCESSING_BATCH_SIZE == 0:
                await db.commit()

        # Final commit
        await db.commit()

        # Telemetry calculations
        duration = time.perf_counter() - start_time
        end_mem = process.memory_info().rss
        mem_usage_mb = (end_mem - start_mem) / (1024 * 1024)
        rows_per_second = round(total_rows / duration, 2) if duration > 0 else total_rows

        report = {
            "file_processed": file_path,
            "total_records": total_rows,
            "successful_inserts": success_count,
            "validation_failures": validation_failures,
            "duplicate_skips": duplicate_skips,
            "incremental_skips": incremental_skips,
            "processing_duration_sec": round(duration, 3),
            "rows_per_second": rows_per_second,
            "memory_delta_mb": round(mem_usage_mb, 2),
        }

        logger.info("processing_dataset_complete", **report)
        return report

pipeline = DatasetPipeline()
