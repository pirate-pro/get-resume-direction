from dataclasses import asdict

from app.crawler.types import NormalizedJob, RawJob
from app.models.enums import EducationLevel, JobType, RemoteType
from app.utils.hash import sha1_hex
from app.utils.location import normalize_location
from app.utils.salary import parse_salary_range
from app.utils.time import now_utc


def normalize_education(text: str | None) -> EducationLevel:
    raw = (text or "").lower()
    if "phd" in raw or "博士" in raw:
        return EducationLevel.phd
    if "master" in raw or "硕士" in raw:
        return EducationLevel.master
    if "bachelor" in raw or "本科" in raw:
        return EducationLevel.bachelor
    if "college" in raw or "大专" in raw:
        return EducationLevel.college
    return EducationLevel.unknown


def normalize_job_type(text: str | None) -> JobType:
    raw = (text or "").lower()
    if "intern" in raw or "实习" in raw:
        return JobType.intern
    if "campus" in raw or "校招" in raw:
        return JobType.campus
    if "part" in raw:
        return JobType.part_time
    if "experienced" in raw or "社招" in raw:
        return JobType.experienced
    if raw:
        return JobType.full_time
    return JobType.unknown


def normalize_remote(text: str | None) -> RemoteType:
    raw = (text or "").lower()
    if "remote" in raw or "远程" in raw:
        return RemoteType.remote
    if "hybrid" in raw or "混合" in raw:
        return RemoteType.hybrid
    if raw:
        return RemoteType.onsite
    return RemoteType.unknown


def normalize_skills(text: str | None) -> list[str]:
    if not text:
        return []
    tokens = [x.strip().lower() for x in text.replace("，", ",").split(",")]
    return sorted({t for t in tokens if t})


def normalize_job(raw: RawJob) -> NormalizedJob:
    salary_min, salary_max, currency, period = parse_salary_range(raw.salary_text)
    province, city, district, normalized_key = normalize_location(raw.city)

    dedup_src = f"{raw.company_name}|{raw.title}|{city or ''}|{(raw.description or '')[:200]}"
    dedup_fingerprint = sha1_hex(dedup_src)

    skills = normalize_skills(raw.skills_text or raw.description)

    normalized = NormalizedJob(
        source_code=raw.source_code,
        external_job_id=raw.external_job_id or f"fp_{dedup_fingerprint}",
        source_url=raw.source_url,
        title=raw.title,
        company_name=raw.company_name,
        province=province,
        city=city,
        district=district,
        location_key=normalized_key,
        salary_min=salary_min,
        salary_max=salary_max,
        salary_currency=currency,
        salary_period=period,
        job_category=raw.job_category,
        seniority=raw.seniority,
        department=raw.department,
        education_requirement=normalize_education(raw.education_requirement),
        experience_min_months=raw.experience_min_months,
        experience_max_months=raw.experience_max_months,
        responsibilities=raw.responsibilities or raw.description,
        qualifications=raw.qualifications,
        tags=raw.tags or [],
        benefits=raw.benefits or [],
        job_type=normalize_job_type(raw.job_type),
        remote_type=normalize_remote(raw.remote_type),
        dedup_fingerprint=dedup_fingerprint,
        global_fingerprint=sha1_hex(f"{raw.company_name}|{raw.title}|{raw.description or ''}"),
        published_at=raw.published_at,
        updated_at_source=raw.updated_at_source,
        first_crawled_at=now_utc(),
        last_crawled_at=now_utc(),
        skills=skills,
    )
    _ = asdict(normalized)
    return normalized
