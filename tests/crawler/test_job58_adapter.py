from app.crawler.adapters.job58_public import Job58PublicAdapter


def test_parse_list_items_extracts_detail_links() -> None:
    html = """
    <html><body>
      <a href="https://bj.58.com/cantfwy/61874462819639x.shtml">传菜员</a>
      <a href="https://bj.58.com/cantfwy/pn2/">下一页</a>
      <a href="https://bj.58.com/job.shtml">职位首页</a>
    </body></html>
    """
    rows = Job58PublicAdapter._parse_list_items(html, category="cantfwy")
    assert len(rows) == 1
    assert rows[0]["external_job_id"] == "61874462819639"
    assert rows[0]["title_hint"] == "传菜员"


def test_parse_raw_job_with_detail_html() -> None:
    adapter = Job58PublicAdapter(
        config={
            "city": "bj",
            "categories": ["cantfwy"],
            "max_pages": 1,
            "max_items": 10,
            "fetch_detail": True,
        }
    )
    detail_html = """
    <html>
      <head>
        <title>传菜员-杭州湘湖新亭子餐饮有限公司_58同城</title>
      </head>
      <body>
        <h1>传菜员</h1>
        <div>4500-5500元/月</div>
        <div>杭州58同城</div>
        <div>学历不限 经验不限</div>
        <div>职位描述：负责餐厅传菜工作，确保菜品及时准确送达。</div>
      </body>
    </html>
    """
    raw = adapter.parse_raw_job(
        list_item={
            "source_url": "https://hz.58.com/cantfwy/61874462819639x.shtml",
            "title_hint": "传菜员",
            "category": "cantfwy",
        },
        detail={"source_url": "https://hz.58.com/cantfwy/61874462819639x.shtml", "html": detail_html},
    )
    assert raw.external_job_id == "61874462819639"
    assert raw.title == "传菜员"
    assert raw.company_name in {"杭州湘湖新亭子餐饮有限公司", "58同城招聘企业"}
    assert raw.salary_text == "4500-5500元/月"
    assert raw.education_requirement == "学历不限"


def test_detect_captcha_page() -> None:
    blocked_html = "<html><title>请输入验证码</title><div>访问过于频繁</div></html>"
    assert Job58PublicAdapter._is_captcha_page(blocked_html) is True
