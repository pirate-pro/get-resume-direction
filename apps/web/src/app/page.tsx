import Link from "next/link";

import { LatestJobs } from "@/features/jobs/components/latest-jobs";

const HOT_CITIES = ["北京", "上海", "深圳", "广州", "杭州"];
const HOT_CATEGORIES = ["后端开发", "数据工程", "算法工程", "测试开发"];

export default function HomePage(): JSX.Element {
  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-brand-100 bg-white p-6 shadow-soft">
        <h1 className="text-3xl font-black tracking-tight text-brand-700">更快找到校招与社招岗位</h1>
        <p className="mt-3 max-w-3xl text-slate-600">
          聚合多平台与高校渠道职位，支持结构化筛选、来源展示与原站跳转。
        </p>

        <form action="/jobs" className="mt-5 grid gap-2 md:max-w-2xl md:grid-cols-[1fr_auto]">
          <label className="sr-only" htmlFor="home-keyword">
            关键词搜索职位
          </label>
          <input
            id="home-keyword"
            name="keyword"
            className="input"
            placeholder="输入岗位、技能或公司关键词..."
          />
          <button type="submit" className="btn-primary">
            搜索职位
          </button>
        </form>

        <div className="mt-3 flex flex-wrap gap-2">
          <Link href="/jobs" className="btn-secondary">
            浏览全部职位
          </Link>
          <Link href="/events" className="btn-secondary">
            浏览校园活动
          </Link>
          <Link href="/orders" className="btn-secondary">
            创建代投订单
          </Link>
          <Link href="/stats" className="btn-secondary">
            查看数据看板
          </Link>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <article className="card">
          <h2 className="text-lg font-bold">热门城市</h2>
          <div className="mt-3 flex flex-wrap gap-2">
            {HOT_CITIES.map((city) => (
              <Link key={city} href={`/jobs?city=${encodeURIComponent(city)}`} className="btn-secondary">
                {city}
              </Link>
            ))}
          </div>
        </article>

        <article className="card">
          <h2 className="text-lg font-bold">热门岗位方向</h2>
          <div className="mt-3 flex flex-wrap gap-2">
            {HOT_CATEGORIES.map((category) => (
              <Link key={category} href={`/jobs?category=${encodeURIComponent(category)}`} className="btn-secondary">
                {category}
              </Link>
            ))}
          </div>
        </article>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <article className="card">
          <h2 className="text-lg font-bold">校园宣讲会与双选会</h2>
          <p className="mt-2 text-sm text-slate-600">按学校、城市、企业筛选线下招聘活动，快速定位可投递场次。</p>
          <Link href="/events" className="btn-primary mt-3">
            去看校园活动
          </Link>
        </article>
        <article className="card">
          <h2 className="text-lg font-bold">线下代投服务</h2>
          <p className="mt-2 text-sm text-slate-600">选择目标公司/活动后直接下单，后续可扩展支付和履约进度。</p>
          <Link href="/orders" className="btn-primary mt-3">
            去下单
          </Link>
        </article>
      </section>

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-xl font-bold">最新职位</h2>
          <Link href="/jobs" className="text-sm font-semibold text-brand-700 hover:underline">
            查看全部
          </Link>
        </div>
        <LatestJobs />
      </section>
    </div>
  );
}
