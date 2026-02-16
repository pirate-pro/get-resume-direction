from app.crawler.base import SiteAdapter
from app.crawler.types import NormalizedJob, RawJob
from app.utils.normalizers import normalize_job


class DemoPlatformAdapter(SiteAdapter):
    source_code = "demo_platform"

    async def fetch_list(self) -> list[dict]:
        return [
            {"job_id": "p-1001", "url": "https://platform.example/jobs/p-1001"},
            {"job_id": "p-1002", "url": "https://platform.example/jobs/p-1002"},
        ]

    async def fetch_detail(self, list_item: dict) -> dict:
        mock_data = {
            "p-1001": {
                "title": "Python Backend Engineer",
                "company": "DemoTech",
                "city": "Shanghai",
                "salary": "25k-40k/月",
                "desc": "FastAPI, PostgreSQL, ETL, async programming",
                "education": "Bachelor",
                "tags": ["backend", "python"],
            },
            "p-1002": {
                "title": "Data Engineer",
                "company": "InsightData",
                "city": "Beijing",
                "salary": "30k-45k/月",
                "desc": "Airflow, Spark, data warehouse",
                "education": "Master",
                "tags": ["data", "etl"],
            },
        }
        return mock_data[list_item["job_id"]]

    def parse_raw_job(self, list_item: dict, detail: dict | str) -> RawJob:
        if not isinstance(detail, dict):
            raise ValueError("Platform adapter expects dict detail")

        return RawJob(
            source_code=self.source_code,
            external_job_id=list_item["job_id"],
            source_url=list_item["url"],
            title=detail["title"],
            company_name=detail["company"],
            city=detail.get("city"),
            salary_text=detail.get("salary"),
            description=detail.get("desc"),
            education_requirement=detail.get("education"),
            tags=detail.get("tags"),
            job_type="full_time",
            remote_type="onsite",
            skills_text=detail.get("desc"),
        )

    def normalize(self, raw: RawJob) -> NormalizedJob:
        return normalize_job(raw)
