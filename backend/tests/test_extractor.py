import pytest
from datetime import date
from app.services.extractor import parse_date, career_extractor
from app.schemas.candidate import ExperienceDetail

def test_parse_date_formats():
    """
    Test that various date string formats are correctly parsed.
    """
    assert parse_date("2020-05-15") == date(2020, 5, 1)
    assert parse_date("2018-09") == date(2018, 9, 1)
    assert parse_date("04/2015") == date(2015, 4, 1)
    assert parse_date("Jan 2021") == date(2021, 1, 1)
    assert parse_date("December 2019") == date(2019, 12, 1)
    assert parse_date("2010") == date(2010, 1, 1)
    assert parse_date("present") == date.today()
    assert parse_date(None) is None

def test_parse_experience_duration_months():
    """
    Test calculating tenure in months.
    """
    exp = ExperienceDetail(
        company_name="Google",
        job_title="SWE",
        start_date="2020-01-01",
        end_date="2020-06-01"
    )
    assert career_extractor.parse_experience_duration_months(exp) == 5

    exp_current = ExperienceDetail(
        company_name="Meta",
        job_title="Research Scientist",
        start_date="2022-01-01",
        end_date="present"
    )
    today = date.today()
    expected_months = (today.year - 2022) * 12 + (today.month - 1)
    assert career_extractor.parse_experience_duration_months(exp_current) == expected_months

def test_extract_timeline_metrics_empty():
    """
    Test extracting metrics when there are no experiences.
    """
    metrics = career_extractor.extract_timeline_metrics([])
    assert metrics["years_experience"] == 0.0
    assert metrics["distinct_companies"] == 0
    assert metrics["average_tenure"] == 0.0
    assert metrics["career_stability"] == 0.0
    assert metrics["employment_gaps"] is False
    assert metrics["promotions_count"] == 0
    assert metrics["current_role"] is None

def test_extract_timeline_metrics_full():
    """
    Test extracting metrics with a realistic experience timeline containing gaps and promotions.
    """
    experiences = [
        ExperienceDetail(
            company_name="Company A",
            job_title="Software Engineer I",
            start_date="2018-01-01",
            end_date="2019-01-01"
        ),
        ExperienceDetail(
            company_name="Company A",
            job_title="Software Engineer II",
            start_date="2019-01-01",
            end_date="2020-01-01"
        ),
        # Gap of 4 months (Jan 2020 to May 2020)
        ExperienceDetail(
            company_name="Company B",
            job_title="Senior Software Engineer",
            start_date="2020-05-01",
            end_date="2022-05-01"
        )
    ]

    metrics = career_extractor.extract_timeline_metrics(experiences)
    # total months: Company A (12 + 12 = 24), Company B (24) -> total 48 months -> 4 years
    assert metrics["years_experience"] == 4.0
    assert metrics["distinct_companies"] == 2
    assert metrics["average_tenure"] == 1.3  # (12 + 12 + 24) months / 3 roles = 16 months = 1.33 years avg
    assert metrics["employment_gaps"] is True
    assert metrics["promotions_count"] == 1  # Software Engineer I -> Software Engineer II at Company A
    assert metrics["current_role"] == "Senior Software Engineer"
