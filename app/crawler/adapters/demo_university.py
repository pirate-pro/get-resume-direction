from app.crawler.base import SiteAdapter
from app.crawler.types import NormalizedJob, RawJob
from app.utils.normalizers import normalize_job


class DemoUniversityAdapter(SiteAdapter):
    source_code = "demo_university"

    async def fetch_list(self) -> list[dict]:
        return [{"notice_id": "u-5001", "url": "https://career.univ.example/notice/u-5001"}]

    async def fetch_detail(self, list_item: dict) -> str:
        return (
            "<html><h1>校园招聘-后端开发工程师</h1><p>公司: CampusTech</p>"
            "<p>城市: 深圳</p><p>薪资: 15k-22k/月</p></html>"
        )

    def parse_raw_job(self, list_item: dict, detail: dict | str) -> RawJob:
        if not isinstance(detail, str):
            raise ValueError("University adapter expects html text")

        return RawJob(
            source_code=self.source_code,
            external_job_id=list_item["notice_id"],
            source_url=list_item["url"],
            title="校园招聘-后端开发工程师",
            company_name="CampusTech",
            city="Shenzhen",
            salary_text="15k-22k/月",
            description="面向校招生，要求计算机基础扎实，了解 Python/FastAPI",
            education_requirement="Bachelor",
            tags=["campus", "backend"],
            job_type="campus",
            remote_type="onsite",
            skills_text="python,fastapi,sql",
        )

    def normalize(self, raw: RawJob) -> NormalizedJob:
        return normalize_job(raw)
