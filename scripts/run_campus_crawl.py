import argparse
import asyncio
import json
import logging
import shutil
from pathlib import Path
from urllib.parse import urlparse

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.crawler.campus_registry import REGISTRY as CAMPUS_REGISTRY
from app.crawler.registry import REGISTRY as JOB_REGISTRY
from app.dao.source_dao import SourceDAO
from app.logging.config import configure_logging
from app.service.campus_crawl_service import CampusCrawlService
from app.service.crawl_service import CrawlService


def _memory_free_ratio() -> float:
    meminfo_path = Path("/proc/meminfo")
    if meminfo_path.exists():
        mem_kv: dict[str, int] = {}
        for line in meminfo_path.read_text(encoding="utf-8").splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            fields = value.strip().split()
            if not fields:
                continue
            try:
                mem_kv[key] = int(fields[0])
            except ValueError:
                continue
        total = mem_kv.get("MemTotal", 0)
        available = mem_kv.get("MemAvailable", mem_kv.get("MemFree", 0))
        if total > 0:
            return available / total
    return 1.0


def _disk_free_ratio(path: str) -> float:
    usage = shutil.disk_usage(path)
    if usage.total <= 0:
        return 1.0
    return usage.free / usage.total


def _resource_snapshot(disk_path: str) -> dict[str, float]:
    return {
        "disk_free_ratio": _disk_free_ratio(disk_path),
        "memory_free_ratio": _memory_free_ratio(),
    }


def _low_resource(snapshot: dict[str, float], min_free_ratio: float) -> bool:
    return (
        snapshot["disk_free_ratio"] < min_free_ratio
        or snapshot["memory_free_ratio"] < min_free_ratio
    )


async def _load_enabled_sources() -> list[str]:
    dao = SourceDAO()
    async with SessionLocal() as session:
        enabled = await dao.list_enabled(session)
        return [source.code for source in enabled]


async def _run_one_source(
    source_code: str,
    crawl_service: CrawlService,
    campus_crawl_service: CampusCrawlService,
) -> dict:
    async with SessionLocal() as session:
        if source_code in JOB_REGISTRY:
            return await crawl_service.run_source(session, source_code=source_code, trigger_type="manual_loop")
        if source_code in CAMPUS_REGISTRY:
            return await campus_crawl_service.run_source(session, source_code=source_code, trigger_type="manual_loop")
        return {"source_code": source_code, "skipped": True, "reason": "adapter_not_registered"}


async def run_loop(
    sources: list[str],
    *,
    min_free_ratio: float,
    disk_path: str,
    interval_seconds: int,
    idle_rounds_to_stop: int,
    max_rounds: int | None,
) -> None:
    crawl_service = CrawlService()
    campus_crawl_service = CampusCrawlService()
    all_enabled = await _load_enabled_sources()
    if sources:
        # Explicitly requested sources should not be silently dropped.
        target_sources = list(dict.fromkeys(sources))
    else:
        target_sources = all_enabled

    if not target_sources:
        print(json.dumps({"message": "no enabled sources to run"}, ensure_ascii=False))
        return

    db_info = _database_target_info()
    print(
        json.dumps(
            {
                "message": "crawler loop started",
                "sources": target_sources,
                "enabled_sources": all_enabled,
                "min_free_ratio": min_free_ratio,
                "interval_seconds": interval_seconds,
                "idle_rounds_to_stop": idle_rounds_to_stop,
                "max_rounds": max_rounds,
                "database_target": db_info,
            },
            ensure_ascii=False,
        )
    )

    round_no = 0
    idle_rounds = 0
    total_inserted = 0
    total_updated = 0

    while True:
        round_no += 1
        snapshot = _resource_snapshot(disk_path)
        if _low_resource(snapshot, min_free_ratio):
            print(
                json.dumps(
                    {
                        "message": "stop_due_to_low_resource",
                        "round": round_no,
                        "snapshot": snapshot,
                        "threshold": min_free_ratio,
                    },
                    ensure_ascii=False,
                )
            )
            break

        round_inserted = 0
        round_updated = 0
        run_results: list[dict] = []

        for source_code in target_sources:
            try:
                result = await _run_one_source(source_code, crawl_service, campus_crawl_service)
                result = {"source_code": source_code, **result}
            except Exception as exc:  # noqa: BLE001
                result = {
                    "source_code": source_code,
                    "status": "failed",
                    "inserted_count": 0,
                    "updated_count": 0,
                    "error": str(exc),
                }
            run_results.append(result)

            if not result.get("skipped"):
                round_inserted += int(result.get("inserted_count", 0) or 0)
                round_updated += int(result.get("updated_count", 0) or 0)

            snapshot = _resource_snapshot(disk_path)
            if _low_resource(snapshot, min_free_ratio):
                print(
                    json.dumps(
                        {
                            "message": "stop_due_to_low_resource",
                            "round": round_no,
                            "source_code": source_code,
                            "snapshot": snapshot,
                            "threshold": min_free_ratio,
                        },
                        ensure_ascii=False,
                    )
                )
                break

        total_inserted += round_inserted
        total_updated += round_updated
        if round_inserted == 0 and round_updated == 0:
            idle_rounds += 1
        else:
            idle_rounds = 0

        print(
            json.dumps(
                {
                    "message": "round_finished",
                    "round": round_no,
                    "round_inserted": round_inserted,
                    "round_updated": round_updated,
                    "idle_rounds": idle_rounds,
                    "total_inserted": total_inserted,
                    "total_updated": total_updated,
                    "results": run_results,
                },
                ensure_ascii=False,
                default=str,
            )
        )

        if idle_rounds >= idle_rounds_to_stop:
            print(
                json.dumps(
                    {
                        "message": "stop_due_to_no_new_data",
                        "round": round_no,
                        "idle_rounds": idle_rounds,
                    },
                    ensure_ascii=False,
                )
            )
            break

        if max_rounds is not None and round_no >= max_rounds:
            print(
                json.dumps(
                    {"message": "stop_due_to_max_rounds", "round": round_no},
                    ensure_ascii=False,
                )
            )
            break

        await asyncio.sleep(interval_seconds)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="持续运行爬虫：直到连续无新增数据，或磁盘/内存剩余低于阈值"
    )
    parser.add_argument(
        "--source",
        action="append",
        default=[],
        help="可传多次，例如 --source yingjiesheng_xjh --source remoteok_real；不传则跑全部启用源",
    )
    parser.add_argument(
        "--min-free-ratio",
        type=float,
        default=0.35,
        help="磁盘/内存最低剩余比例阈值，默认 0.35 (35%%)",
    )
    parser.add_argument(
        "--disk-path",
        default="/",
        help="磁盘空间检测路径，默认 /",
    )
    parser.add_argument(
        "--interval-seconds",
        type=int,
        default=30,
        help="每轮抓取间隔秒数，默认 30 秒",
    )
    parser.add_argument(
        "--idle-rounds-to-stop",
        type=int,
        default=3,
        help="连续无新增轮次达到该值后停止，默认 3",
    )
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=None,
        help="可选，最大轮次（用于调试）",
    )
    parser.add_argument(
        "--log-level",
        default=None,
        help="可选，日志级别（DEBUG/INFO/WARNING/ERROR），默认读取 APP_LOG_LEVEL",
    )
    return parser.parse_args()


def _database_target_info() -> dict[str, str]:
    settings = get_settings()
    parsed = urlparse(settings.database_url)
    host = parsed.hostname or ""
    port = str(parsed.port or "")
    db_name = parsed.path.lstrip("/") if parsed.path else ""
    return {"host": host, "port": port, "database": db_name}


async def main() -> None:
    args = parse_args()
    settings = get_settings()
    configure_logging(args.log_level or settings.log_level)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    min_free_ratio = max(0.01, min(0.95, args.min_free_ratio))
    await run_loop(
        sources=args.source,
        min_free_ratio=min_free_ratio,
        disk_path=args.disk_path,
        interval_seconds=args.interval_seconds,
        idle_rounds_to_stop=args.idle_rounds_to_stop,
        max_rounds=args.max_rounds,
    )


if __name__ == "__main__":
    asyncio.run(main())
