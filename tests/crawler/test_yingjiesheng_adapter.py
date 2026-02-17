from datetime import timezone

from app.crawler.adapters.yingjiesheng_xjh import YingJieShengXjhAdapter
from app.utils.time import now_utc


def test_parse_legacy_rows_extracts_event_id_and_fields() -> None:
    html = """
    <table cellpadding="2" cellspacing="0" class="li">
      <tr>
        <td width="100" align="center">
          <a href="/xuanjianghui_city_29.html" target="_blank" class="i i_gray">深圳</a>
        </td>
        <td width="120" align="center"><span class="i">2026-03-02<br>(周一)</span></td>
        <td width="280" id="r_comments_e6229124">
          <a href="/xjh-006-229-124.html" target="_blank" class="i i_blue">维沃移动通信有限公司</a>
        </td>
        <td width="240"><a href="/xuanjianghui_school_1600.html" class="i i_blue">南方科技大学</a></td>
        <td width="290"><span class="i">南科大中心201多功能厅</span></td>
      </tr>
    </table>
    """
    adapter = YingJieShengXjhAdapter(config={"fetch_detail": False, "include_legacy_html": False})
    rows = adapter._parse_legacy_rows(html)
    assert len(rows) == 1
    row = rows[0]
    assert row["external_event_id"] == "6229124"
    assert row["city"] == "深圳"
    assert row["title"] == "维沃移动通信有限公司"
    assert row["school_name"] == "南方科技大学"
    assert row["venue"] == "南科大中心201多功能厅"
    assert row["source_url"].endswith("/xjh-006-229-124.html")


def test_build_event_from_legacy_row_infers_event_type() -> None:
    adapter = YingJieShengXjhAdapter(config={"fetch_detail": False, "include_legacy_html": False})
    now = now_utc()
    row = {
        "external_event_id": "6229644",
        "date_text": "2026-03-05",
        "city": "成都",
        "title": "【春季学期第一场】西南石油大学2026届毕业生春季系列双选会",
        "school_name": "西南石油大学",
        "venue": "校园招聘大厅",
        "source_url": "https://my.yingjiesheng.com/xjh-006-229-644.html",
    }
    event = adapter._build_event_from_legacy_row(now=now, row=row)
    assert event is not None
    assert event.external_event_id == "6229644"
    assert event.event_type == "job_fair"
    assert event.source_url == row["source_url"]
    assert event.starts_at is not None
    assert event.starts_at.tzinfo == timezone.utc
