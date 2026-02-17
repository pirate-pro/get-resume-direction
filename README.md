# China Campus Job Aggregator

基于 FastAPI + PostgreSQL + SQLAlchemy 2.0 + Alembic + APScheduler + Next.js 的校园/社招职位聚合平台（MVP）。

## Monorepo

- 后端：`app/`（Python，`uv`）
- 前端：`apps/web/`（Next.js，`npm`）

## 已落地能力（当前）

- 职位聚合：职位列表、详情、筛选、统计
- 校园活动：宣讲会/招聘会活动聚合、活动详情、活动统计
- 订单链路：创建代投订单、按手机号查询订单、订单详情
- 爬虫任务：手动触发 + 定时调度 + 失败记录 + 风险自动降级（可暂停源）
- 中文 UI：`/events`、`/orders`、`/stats` 已接入后端 API

## 快速启动（后端）

1. 安装依赖
   - `uv sync`
2. 配置环境变量
   - `cp .env.example .env`
   - 按实际数据库修改 `APP_DATABASE_URL`
3. 执行迁移
   - `uv run alembic upgrade head`
4. 初始化数据源配置
   - `uv run python scripts/seed_sources.py`
5. 启动后端
   - `uv run uvicorn app.main:app --host 0.0.0.0 --port 8000`

## 真实活动抓取（应届生）

- 持续抓取（默认）：
  - `uv run python scripts/run_campus_crawl.py --source yingjiesheng_xjh`
- 该脚本会一直运行，直到满足任一条件：
  - 连续无新增数据达到阈值（默认 3 轮）
  - 磁盘或内存剩余比例低于阈值（默认 35%）
- 常用参数：
  - `--min-free-ratio 0.35`
  - `--idle-rounds-to-stop 3`
  - `--interval-seconds 30`
  - `--max-rounds 1`（调试单轮）
- 说明：
  - 适配器默认采用“`youngapi` + 老站分页列表”双通道抓取，提升覆盖度
  - 支持线下宣讲（`kxType=0`）和空中宣讲（`kxType=1`）
  - 默认会补抓详情接口，拿到宣讲会详细描述字段
  - 每轮结果会输出 `crawl_meta`，可直接看到各通道分页数、抓取量与去重后增量
  - 数据源配置在 `scripts/seed_sources.py` 与 `configs/sites.yaml`

## 招聘站真实职位抓取（BOSS/智联/51job/58）

- 已提供适配器：
  - `zhipin_public`
  - `zhaopin_public`
  - `job51_public`
  - `job58_public`
- 三者均为风控敏感源，默认 `enabled=false`，未提供登录态 Cookie 时通常会触发验证/空结果。
- 登录并复制 Cookie 后，可直接写入配置并启用：
  - `uv run python scripts/set_source_cookie.py --source zhipin_public --cookie 'xxx=...; yyy=...' --enable`
  - `uv run python scripts/set_source_cookie.py --source zhaopin_public --cookie 'xxx=...; yyy=...' --enable`
  - `uv run python scripts/set_source_cookie.py --source job51_public --cookie 'xxx=...; yyy=...' --enable`
  - `uv run python scripts/set_source_cookie.py --source job58_public --cookie 'xxx=...; yyy=...' --enable`
- 单源触发抓取：
  - `uv run python scripts/run_campus_crawl.py --source zhipin_public --max-rounds 1`
  - `uv run python scripts/run_campus_crawl.py --source zhaopin_public --max-rounds 1`
  - `uv run python scripts/run_campus_crawl.py --source job51_public --max-rounds 1`
  - `uv run python scripts/run_campus_crawl.py --source job58_public --max-rounds 1`
- 58 说明：
  - 当前环境若返回“请输入验证码/访问过于频繁”，需提供 `APP_JOB58_COOKIE` 或可用代理后再抓取
  - 适配器支持按城市+类目+分页抓取，并下钻详情页解析职位描述/薪资/公司信息
- 51job `vapi.51job.com` 方案（你抓到 `type__1260` + form body 后）：
  - `uv run python scripts/set_job51_vapi_profile.py --type-token 'xxx' --account-id 'xxx' --form 'a=1&b=2&page=1&page_size=20&keyword=后端' --cookie 'k=v; ...' --enable`
  - 若返回 `签名不正确` / `status=10002`，说明 `type__1260` 已失效，需要重新抓最新请求。

## API 示例

- 活动列表：
  - `GET /api/v1/campus-events?page=1&page_size=20`
- 活动详情：
  - `GET /api/v1/campus-events/{event_id}`
- 活动统计：
  - `GET /api/v1/campus-events/stats/basic`
- 创建订单：
  - `POST /api/v1/orders`
- 订单列表：
  - `GET /api/v1/orders?page=1&page_size=20&phone=13800000000`

## 前端启动（Next.js）

1. 安装依赖
   - `cd apps/web && npm i`
2. 配置后端地址
   - `cp .env.example .env.local`
   - 设置 `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`
3. 启动前端
   - `npm run dev`
4. 核心页面
   - 首页：`/`
   - 职位：`/jobs`
   - 校园活动：`/events`
   - 订单中心：`/orders`
   - 数据看板：`/stats`

## 测试与质量

- 前端类型检查：`npm --prefix apps/web run typecheck`
- 前端测试：`npm --prefix apps/web run test`
- 后端快速语法检查：`python3 -m compileall app scripts`
