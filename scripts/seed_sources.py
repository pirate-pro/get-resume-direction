import asyncio

from sqlalchemy.dialects.postgresql import insert

from app.core.database import SessionLocal
from app.models.source import Source

SOURCES = [
    {
        "code": "demo_platform",
        "name": "Demo Recruiting Platform",
        "source_type": "platform",
        "enabled": False,
        "robots_allowed": True,
        "config_json": {
            "schedule_cron": "*/30 * * * *",
            "throttle": {"qps": 1.0, "concurrency": 2, "jitter_ms": 200},
            "retry": {"max_attempts": 3, "backoff_seconds": 1.0},
            "allow_paths": ["/jobs"],
            "deny_paths": ["/captcha", "/login"],
        },
    },
    {
        "code": "demo_university",
        "name": "Demo University Career Site",
        "source_type": "university",
        "enabled": False,
        "robots_allowed": True,
        "config_json": {
            "schedule_cron": "15 */1 * * *",
            "throttle": {"qps": 0.5, "concurrency": 1, "jitter_ms": 500},
            "retry": {"max_attempts": 2, "backoff_seconds": 2.0},
            "allow_paths": ["/career", "/notice"],
            "deny_paths": ["/captcha", "/login"],
        },
    },
    {
        "code": "remoteok_real",
        "name": "RemoteOK Real Jobs API",
        "source_type": "platform",
        "enabled": True,
        "robots_allowed": True,
        "config_json": {
            "schedule_cron": "*/45 * * * *",
            "throttle": {"qps": 0.5, "concurrency": 1, "jitter_ms": 300},
            "retry": {"max_attempts": 3, "backoff_seconds": 2.0},
            "allow_paths": ["/api"],
            "deny_paths": [],
            "trust_env": False,
            "proxy_url": None,
            "attribution": "Data source: RemoteOK (https://remoteok.com)",
        },
    },
    {
        "code": "iguopin_jobs",
        "name": "国聘职位",
        "source_type": "platform",
        "enabled": True,
        "robots_allowed": True,
        "config_json": {
            "schedule_cron": "*/20 * * * *",
            "throttle": {"qps": 0.6, "concurrency": 1, "jitter_ms": 200},
            "retry": {"max_attempts": 4, "backoff_seconds": 2.0},
            "allow_paths": ["/api/jobs/v1/"],
            "deny_paths": [],
            "base_url": "https://gp-api.iguopin.com",
            "site_url": "https://www.iguopin.com",
            "list_path": "/api/jobs/v1/list",
            "detail_path": "/api/jobs/v1/info",
            "job_natures": ["113Fc6wc", "114BeBeq", "115xW5oQ", "11bTac9"],
            "page_size": 30,
            "max_pages": 60,
            "max_items": 3000,
            "fetch_detail": False,
            "timeout_seconds": 20,
            "retry_count": 4,
            "request_interval_seconds": 0.2,
            "trust_env": False,
            "proxy_url": None,
            "headers": {
                "User-Agent": "Mozilla/5.0",
                "Device": "pc",
                "Version": "5.2.300",
                "Subsite": "iguopin"
            },
            "attribution": "Data source: 国聘职位接口 (https://gp-api.iguopin.com, https://www.iguopin.com)",
        },
    },
    {
        "code": "zhipin_public",
        "name": "BOSS直聘公开检索（风控敏感）",
        "source_type": "platform",
        "enabled": False,
        "robots_allowed": True,
        "config_json": {
            "schedule_cron": "0 */4 * * *",
            "throttle": {"qps": 0.2, "concurrency": 1, "jitter_ms": 500},
            "retry": {"max_attempts": 3, "backoff_seconds": 3.0},
            "allow_paths": ["/wapi/zpgeek/search/"],
            "deny_paths": ["/captcha", "/verify", "/login"],
            "api_url": "https://www.zhipin.com/wapi/zpgeek/search/joblist.json",
            "city": "101280600",
            "keywords": ["校招", "后端", "实习"],
            "page_size": 30,
            "max_pages": 10,
            "fail_on_empty": True,
            "timeout_seconds": 20,
            "retry_count": 3,
            "request_interval_seconds": 0.35,
            "trust_env": False,
            "proxy_url": None,
            "attribution": "Data source: BOSS直聘公开页面接口（需遵守平台规则）",
        },
    },
    {
        "code": "zhaopin_public",
        "name": "智联招聘公开检索（风控敏感）",
        "source_type": "platform",
        "enabled": False,
        "robots_allowed": True,
        "config_json": {
            "schedule_cron": "10 */4 * * *",
            "throttle": {"qps": 0.2, "concurrency": 1, "jitter_ms": 500},
            "retry": {"max_attempts": 3, "backoff_seconds": 3.0},
            "allow_paths": ["/c/i/sou"],
            "deny_paths": ["/captcha", "/verify", "/login"],
            "api_url": "https://fe-api.zhaopin.com/c/i/sou",
            "base_params": {
                "cityId": "530",
                "workExperience": "-1",
                "education": "-1",
                "companyType": "-1",
                "employmentType": "-1",
                "jobWelfareTag": "-1"
            },
            "keywords": ["校招", "后端", "实习"],
            "page_size": 30,
            "max_pages": 10,
            "fail_on_empty": True,
            "timeout_seconds": 20,
            "retry_count": 3,
            "request_interval_seconds": 0.35,
            "trust_env": False,
            "proxy_url": None,
            "headers": {
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json, text/plain, */*",
                "Referer": "https://sou.zhaopin.com/"
            },
            "cookies": {},
            "cookie_env": "APP_ZHAOPIN_COOKIE",
            "attribution": "Data source: 智联招聘公开接口（需登录态并遵守平台规则）",
        },
    },
    {
        "code": "job51_public",
        "name": "51job公开检索（风控敏感）",
        "source_type": "platform",
        "enabled": False,
        "robots_allowed": True,
        "config_json": {
            "schedule_cron": "20 */4 * * *",
            "throttle": {"qps": 0.2, "concurrency": 1, "jitter_ms": 500},
            "retry": {"max_attempts": 3, "backoff_seconds": 3.0},
            "allow_paths": ["/api/job/search-pc"],
            "deny_paths": ["/captcha", "/verify", "/login"],
            "api_url": "https://we.51job.com/api/job/search-pc",
            "base_params": {
                "searchType": "2",
                "sortType": "0"
            },
            "keywords": ["校招", "后端", "实习"],
            "page_size": 20,
            "max_pages": 10,
            "timeout_seconds": 20,
            "retry_count": 3,
            "request_interval_seconds": 0.45,
            "trust_env": False,
            "proxy_url": None,
            "headers": {
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json, text/plain, */*",
                "Referer": "https://we.51job.com/pc/search"
            },
            "cookies": {},
            "cookie_env": "APP_JOB51_COOKIE",
            "attribution": "Data source: 51job公开接口（需登录态并遵守平台规则）",
        },
    },
    {
        "code": "job58_public",
        "name": "58同城公开职位（风控敏感）",
        "source_type": "platform",
        "enabled": False,
        "robots_allowed": True,
        "config_json": {
            "schedule_cron": "30 */4 * * *",
            "throttle": {"qps": 0.2, "concurrency": 1, "jitter_ms": 600},
            "retry": {"max_attempts": 3, "backoff_seconds": 3.0},
            "allow_paths": ["/job/", "/pn", ".shtml"],
            "deny_paths": ["/captcha", "/verify", "/firewall"],
            "homepage_url": "https://www.58.com/job/",
            "city": "bj",
            "categories": ["cantfwy", "yewu", "caiwu", "xzbgs", "jiajiao"],
            "max_pages": 8,
            "max_items": 300,
            "fetch_detail": True,
            "fail_on_empty": True,
            "timeout_seconds": 20,
            "retry_count": 3,
            "request_interval_seconds": 0.35,
            "detail_request_interval_seconds": 0.1,
            "trust_env": False,
            "proxy_url": None,
            "headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Referer": "https://www.58.com/job/"
            },
            "cookies": {},
            "cookie_env": "APP_JOB58_COOKIE",
            "attribution": "Data source: 58同城公开职位页面（需遵守平台规则）",
        },
    },
    {
        "code": "yingjiesheng_xjh",
        "name": "应届生宣讲会",
        "source_type": "university",
        "enabled": True,
        "robots_allowed": True,
        "config_json": {
            "schedule_cron": "*/30 * * * *",
            "throttle": {"qps": 0.3, "concurrency": 1, "jitter_ms": 300},
            "retry": {"max_attempts": 3, "backoff_seconds": 2.0},
            "allow_paths": ["/open/noauth/yjs/xjh/"],
            "deny_paths": [],
            "api_base_url": "https://youngapi.yingjiesheng.com",
            "landing_url": "https://www.yingjiesheng.com/",
            "api_version": "2.3.5",
            "api_key": "xy",
            "from_domain": "yjs_web",
            "page_size": 200,
            "max_pages": 50,
            "kx_types": [0, 1],
            "fetch_detail": True,
            "include_legacy_html": True,
            "legacy_list_url_template": "https://my.yingjiesheng.com/index.php/personal/xjhinfo.htm/?page={page}&cid=&city=0&word=&province=0&schoolid=&sdate=&hyid=0",
            "legacy_max_pages": 30,
            "legacy_request_interval_seconds": 0.1,
            "timeout_seconds": 20,
            "retry_count": 3,
            "request_interval_seconds": 0.1,
            "trust_env": False,
            "proxy_url": None,
            "attribution": "Data source: 应届生求职网开放接口 + 老站宣讲会列表 (https://youngapi.yingjiesheng.com, https://my.yingjiesheng.com)",
        },
    },
    {
        "code": "iguopin_campus",
        "name": "国聘校园活动",
        "source_type": "university",
        "enabled": False,
        "robots_allowed": True,
        "config_json": {
            "schedule_cron": "0 */2 * * *",
            "throttle": {"qps": 0.5, "concurrency": 1, "jitter_ms": 200},
            "retry": {"max_attempts": 3, "backoff_seconds": 2.0},
            "allow_paths": ["/api/activity"],
            "deny_paths": ["/captcha", "/login"],
            "attribution": "Data source: 国聘校园活动 (https://xiaoyuan.iguopin.com)",
        },
    },
]


async def main() -> None:
    async with SessionLocal() as session:
        for source in SOURCES:
            stmt = insert(Source).values(**source)
            stmt = stmt.on_conflict_do_update(
                index_elements=[Source.code],
                set_={
                    "name": source["name"],
                    "source_type": source["source_type"],
                    "enabled": source["enabled"],
                    "robots_allowed": source["robots_allowed"],
                    "config_json": source["config_json"],
                },
            )
            await session.execute(stmt)
        await session.commit()


if __name__ == "__main__":
    asyncio.run(main())
