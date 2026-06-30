import sys
import os
import argparse
import asyncio
import json
import csv

# Fix sys.path to run script from backend folder or scripts folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import async_session_factory
from app.database.repositories.job import JobRepository
from app.database.repositories.candidate import CandidateRepository
from app.database.repositories.explanation import ExplanationRepository
from app.services.explainability.pdf_exporter import SimplePDFExporter
from app.services.agents.explainability_agent import explainability_agent

async def main():
    parser = argparse.ArgumentParser(description="Generate candidate recruiter report in multiple formats (PDF, JSON, CSV, MD).")
    parser.add_argument("--job_id", help="Job Description ID. If omitted, takes first job in DB.")
    parser.add_argument("--candidate_id", help="Candidate ID. If omitted, takes the top candidate.")
    parser.add_argument("--format", choices=["pdf", "json", "csv", "md"], default="pdf", help="Report format.")
    parser.add_argument("--output", help="Optional custom output filename.")

    args = parser.parse_args()
    job_id = args.job_id
    candidate_id = args.candidate_id
    fmt = args.format.lower()

    async with async_session_factory() as session:
        job_repo = JobRepository(session)
        cand_repo = CandidateRepository(session)
        exp_repo = ExplanationRepository(session)

        # 1. Resolve Job ID
        if not job_id:
            all_jobs = await job_repo.get_all()
            if not all_jobs:
                print("Error: No jobs in database.")
                sys.exit(1)
            job_id = all_jobs[0].id
            print(f"No Job ID specified. Using first job: ID '{job_id}' ({all_jobs[0].title})")
        else:
            job = await job_repo.get_by_id(job_id)
            if not job:
                print(f"Error: Job description '{job_id}' not found.")
                sys.exit(1)

        # Ensure explanation generated
        print(f"Ensuring explanations are generated for Job ID '{job_id}'...")
        await explainability_agent.initialize()
        context = {"db": session}
        if candidate_id:
            context["candidate_ids"] = [candidate_id]
        await explainability_agent.execute(job_id, context)
        await session.commit()

        # 2. Fetch target candidate explanation
        exps = await exp_repo.get_all_for_job(job_id)
        if not exps:
            print("Error: No explanations found in database.")
            sys.exit(1)

        target_exp = None
        if candidate_id:
            for e in exps:
                if e.candidate_id == candidate_id:
                    target_exp = e
                    break
            if not target_exp:
                print(f"Error: Explanation for candidate '{candidate_id}' under job '{job_id}' not found.")
                sys.exit(1)
        else:
            # Take top candidate by match percentage
            exps_sorted = sorted(exps, key=lambda x: x.explanation_package.get("match_percentage", 0.0), reverse=True)
            target_exp = exps_sorted[0]
            candidate_id = target_exp.candidate_id

        cand_profile = await cand_repo.get_candidate_profile(candidate_id)
        cand_name = f"{cand_profile.first_name} {cand_profile.last_name}" if cand_profile else "Candidate Profile"

        pkg = target_exp.explanation_package
        breakdown = target_exp.match_breakdown
        audit = target_exp.audit_trail

        os.makedirs("exports", exist_ok=True)
        filepath = args.output or f"exports/recruiter_report_{job_id}_{candidate_id}.{fmt}"

        # 3. Export to different formats
        if fmt == "pdf":
            job = await job_repo.get_by_id(job_id)
            job_title = job.title if job else "Software Engineer"
            
            exporter = SimplePDFExporter()
            exporter.generate_candidate_report(
                filepath=filepath,
                title=f"{cand_name} - {job_title}",
                narrative=pkg["overall_summary"],
                strengths=pkg["strengths"],
                weaknesses=pkg["weaknesses"],
                interview_plan={"interview_focus_areas": pkg["interview_recommendation"]}
            )

        elif fmt == "json":
            report_data = {
                "candidate_id": candidate_id,
                "candidate_name": cand_name,
                "job_id": job_id,
                "overall_score": pkg.get("match_percentage"),
                "hiring_confidence": pkg.get("hiring_confidence"),
                "recommendation": audit.get("recommendation"),
                "narrative": pkg.get("overall_summary"),
                "scores_breakdown": breakdown,
                "strengths": pkg.get("strengths"),
                "weaknesses": pkg.get("weaknesses"),
                "missing_skills": pkg.get("missing_skills"),
                "transferable_skills": pkg.get("transferable_skills"),
                "interview_plan": pkg.get("interview_recommendation"),
                "audit_trail": audit
            }
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=2)

        elif fmt == "csv":
            # Flatten data into key-value format for CSV
            strengths_str = "; ".join([f"[{s.get('category')}] {s.get('name')}" for s in pkg.get("strengths", [])])
            weaknesses_str = "; ".join([f"[{w.get('category')}] {w.get('name')}" for w in pkg.get("weaknesses", [])])
            
            missing_skills_list = []
            for severity, items in pkg.get("missing_skills", {}).items():
                for item in items:
                    missing_skills_list.append(f"{item.get('name')} ({severity.split('_')[0]})")
            missing_skills_str = "; ".join(missing_skills_list)

            interview_plan_str = "; ".join([
                f"Topic: {area.get('topic')} (Q: {' / '.join(area.get('questions', []))})"
                for area in pkg.get("interview_recommendation", [])
            ])

            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Field Name", "Value"])
                writer.writerow(["Candidate ID", candidate_id])
                writer.writerow(["Candidate Name", cand_name])
                writer.writerow(["Job ID", job_id])
                writer.writerow(["Overall Match Percentage", f"{pkg.get('match_percentage', 0.0):.1f}%"])
                writer.writerow(["Hiring Confidence", f"{pkg.get('hiring_confidence', 0.0)*100:.0f}%"])
                writer.writerow(["Hiring Recommendation", audit.get("recommendation", "Interview")])
                writer.writerow(["Hiring Narrative", pkg.get("overall_summary", "")])
                writer.writerow(["Scores Breakdown (Semantic)", f"{breakdown.get('semantic', {}).get('normalized_score', 0.0):.1f}%"])
                writer.writerow(["Scores Breakdown (Skills)", f"{breakdown.get('skills', {}).get('normalized_score', 0.0):.1f}%"])
                writer.writerow(["Scores Breakdown (Career)", f"{breakdown.get('career', {}).get('normalized_score', 0.0):.1f}%"])
                writer.writerow(["Scores Breakdown (Leadership)", f"{breakdown.get('leadership', {}).get('normalized_score', 0.0):.1f}%"])
                writer.writerow(["Scores Breakdown (Projects)", f"{breakdown.get('projects', {}).get('normalized_score', 0.0):.1f}%"])
                writer.writerow(["Scores Breakdown (Potential)", f"{breakdown.get('potential', {}).get('normalized_score', 0.0):.1f}%"])
                writer.writerow(["Scores Breakdown (Risk Penalty)", f"{breakdown.get('risk', {}).get('penalty_applied', 0.0):.1f}%"])
                writer.writerow(["Top Strengths", strengths_str])
                writer.writerow(["Identified Gaps", weaknesses_str])
                writer.writerow(["Missing Skills", missing_skills_str])
                writer.writerow(["Interview Plan Focus Areas", interview_plan_str])

        elif fmt == "md":
            md_lines = [
                f"# Recruiter Audit Report: {cand_name}",
                f"**Job ID**: `{job_id}` | **Candidate ID**: `{candidate_id}`",
                "",
                "## Overall Evaluation",
                f"- **Overall Match**: {pkg.get('match_percentage', 0.0):.1f}%",
                f"- **Hiring Confidence**: {pkg.get('hiring_confidence', 0.0)*100:.0f}%",
                f"- **Recommendation**: **{audit.get('recommendation', 'Interview')}**",
                "",
                "### Hiring Narrative",
                pkg.get("overall_summary", ""),
                "",
                "## Match Breakdown",
                "| Dimension | Score |",
                "|---|---|",
                f"| Semantic Match | {breakdown.get('semantic', {}).get('normalized_score', 0.0):.1f}% |",
                f"| Skills Match | {breakdown.get('skills', {}).get('normalized_score', 0.0):.1f}% |",
                f"| Career Match | {breakdown.get('career', {}).get('normalized_score', 0.0):.1f}% |",
                f"| Projects Match | {breakdown.get('projects', {}).get('normalized_score', 0.0):.1f}% |",
                f"| Leadership Match | {breakdown.get('leadership', {}).get('normalized_score', 0.0):.1f}% |",
                f"| Potential Match | {breakdown.get('potential', {}).get('normalized_score', 0.0):.1f}% |",
                f"| Risk Penalty | {breakdown.get('risk', {}).get('penalty_applied', 0.0):.1f}% |",
                "",
                "## Key Strengths (Evidence-Backed)",
            ]
            for i, s in enumerate(pkg.get("strengths", []), 1):
                md_lines.append(f"### {i}. [{s.get('category')}] {s.get('name')}")
                md_lines.append(f"- **Impact**: {s.get('impact')}")
                md_lines.append(f"- **Evidence**: {s.get('evidence')}")
                md_lines.append("")

            md_lines.append("## Identified Gaps & Risks")
            weaks = pkg.get("weaknesses", [])
            if weaks:
                for i, w in enumerate(weaks, 1):
                    md_lines.append(f"### {i}. [{w.get('category')}] {w.get('name')}")
                    md_lines.append(f"- **Severity**: {w.get('severity')}")
                    md_lines.append(f"- **Evidence**: {w.get('evidence')}")
                    md_lines.append("")
            else:
                md_lines.append("- No significant gaps or risks identified.")
                md_lines.append("")

            md_lines.append("## Missing & Transferable Skills")
            missing = pkg.get("missing_skills", {})
            for severity in ["critical_missing", "important_missing", "nice_to_have_missing"]:
                items = missing.get(severity, [])
                if items:
                    md_lines.append(f"### {severity.replace('_', ' ').title()}")
                    for item in items:
                        md_lines.append(f"- **{item.get('name')}** (Est. Learning Effort: {item.get('learning_effort')})")
                        md_lines.append(f"  - *Suggestion*: {item.get('actionable_suggestion')}")
                    md_lines.append("")

            trans = pkg.get("transferable_skills", [])
            if trans:
                md_lines.append("### Transferable Skills Mapping")
                for t in trans:
                    md_lines.append(f"- **Missing Skill**: {t.get('missing_skill')} -> **Transferable Alternative**: {t.get('transferable_skill')}")
                    md_lines.append(f"  - *Reasoning*: {t.get('explanation')}")
                md_lines.append("")

            md_lines.append("## Interview Recommendation Plan")
            focus_areas = pkg.get("interview_recommendation", [])
            for i, area in enumerate(focus_areas, 1):
                md_lines.append(f"### Focus Area {i}: {area.get('topic')}")
                for q in area.get("questions", []):
                    md_lines.append(f"- Q: {q}")
                md_lines.append("")

            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(md_lines))

        print(f"Report successfully generated in {fmt.upper()} format at: {os.path.abspath(filepath)}")

if __name__ == "__main__":
    asyncio.run(main())
