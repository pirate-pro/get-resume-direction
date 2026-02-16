from app.crawler.types import RawJob
from app.utils.normalizers import normalize_job


def test_normalize_job_generates_fingerprint() -> None:
    raw = RawJob(
        source_code="demo_platform",
        external_job_id="p-1",
        source_url="https://example/jobs/p-1",
        title="Backend Engineer",
        company_name="Demo",
        city="Shanghai",
        salary_text="20k-30k/月",
        description="python,fastapi,postgres",
        education_requirement="Bachelor",
        job_type="full_time",
        remote_type="onsite",
    )
    job = normalize_job(raw)
    assert job.dedup_fingerprint
    assert job.location_key.startswith("cn::")
