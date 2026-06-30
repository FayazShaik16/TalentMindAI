import re
from datetime import date, datetime
from collections.abc import Sequence
from app.schemas.candidate import ExperienceDetail

def parse_date(date_val: str | datetime | None) -> date | None:
    """
    Parses dates in common formats (YYYY-MM-DD, YYYY-MM, MM/YYYY, Text Months, YYYY)
    falling back to today for current indicators.
    """
    if not date_val:
        return None
    if isinstance(date_val, datetime):
        return date_val.date()
    if isinstance(date_val, date):
        return date_val

    d_str = date_val.strip().lower()
    if d_str in ["present", "current", "now", "today", ""]:
        return date.today()

    # Regex matches
    # 1. YYYY-MM-DD or YYYY-MM
    match1 = re.match(r"^(\d{4})-(\d{1,2})", d_str)
    if match1:
        return date(int(match1.group(1)), int(match1.group(2)), 1)

    # 2. MM/YYYY
    match2 = re.match(r"^(\d{1,2})/(\d{4})", d_str)
    if match2:
        return date(int(match2.group(2)), int(match2.group(1)), 1)

    # 3. Text Month YYYY (e.g. "January 2021" or "Jan 2021")
    months = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
        "january": 1, "february": 2, "march": 3, "april": 4, "june": 6,
        "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12
    }
    match3 = re.match(r"^([a-zA-Z]+)\s+(\d{4})", d_str)
    if match3:
        m_prefix = match3.group(1)[:3]
        if m_prefix in months:
            return date(int(match3.group(2)), months[m_prefix], 1)

    # 4. YYYY
    match4 = re.match(r"^(\d{4})", d_str)
    if match4:
        return date(int(match4.group(1)), 1, 1)

    return None

class CareerTimelineExtractor:
    @staticmethod
    def parse_experience_duration_months(exp: ExperienceDetail) -> int:
        s_date = parse_date(exp.start_date)
        e_date = parse_date(exp.end_date) or date.today()

        if not s_date:
            return 0

        delta = (e_date.year - s_date.year) * 12 + (e_date.month - s_date.month)
        return max(0, delta)

    def extract_timeline_metrics(self, experiences: Sequence[ExperienceDetail]) -> dict:
        """
        Traces candidate experience records to compute tenure metrics, career gaps, and promotions.
        """
        if not experiences:
            return {
                "years_experience": 0.0,
                "distinct_companies": 0,
                "average_tenure": 0.0,
                "career_stability": 0.0,
                "employment_gaps": False,
                "promotions_count": 0,
                "current_role": None,
            }

        # Filter and sort experiences by start date
        sorted_exps = sorted(
            [e for e in experiences if parse_date(e.start_date) is not None],
            key=lambda x: parse_date(x.start_date) or date.min
        )

        total_months = 0
        companies = set()
        tenures = []
        promotions = 0
        gaps_detected = False
        prev_end_date = None
        company_titles = {}

        for exp in sorted_exps:
            comp_clean = exp.company_name.strip().lower()
            companies.add(comp_clean)

            # Detect promotion tracks
            if comp_clean in company_titles:
                if exp.job_title.lower() != company_titles[comp_clean][-1].lower():
                    promotions += 1
                company_titles[comp_clean].append(exp.job_title)
            else:
                company_titles[comp_clean] = [exp.job_title]

            dur_months = self.parse_experience_duration_months(exp)
            total_months += dur_months
            tenures.append(dur_months / 12.0)

            # Check for employment gaps (> 3 months)
            s_date = parse_date(exp.start_date)
            if prev_end_date and s_date:
                gap = (s_date.year - prev_end_date.year) * 12 + (s_date.month - prev_end_date.month)
                if gap > 3:
                    gaps_detected = True

            prev_end_date = parse_date(exp.end_date) or date.today()

        avg_tenure = sum(tenures) / len(tenures) if tenures else 0.0
        stability_score = min(100.0, avg_tenure * 20.0)  # 5 years average = 100% score

        current_role = sorted_exps[-1].job_title if sorted_exps else None

        return {
            "years_experience": round(total_months / 12.0, 1),
            "distinct_companies": len(companies),
            "average_tenure": round(avg_tenure, 1),
            "career_stability": round(stability_score, 1),
            "employment_gaps": gaps_detected,
            "promotions_count": promotions,
            "current_role": current_role,
        }

career_extractor = CareerTimelineExtractor()
