import Link from "next/link";

import { LatestJobs } from "@/features/jobs/components/latest-jobs";

const HOT_CITIES = ["Beijing", "Shanghai", "Shenzhen", "Guangzhou", "Hangzhou"];
const HOT_CATEGORIES = ["Backend Engineering", "Data Engineering", "Algorithm Engineering", "QA"];

export default function HomePage(): JSX.Element {
  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-brand-100 bg-white p-6 shadow-soft">
        <h1 className="text-3xl font-black tracking-tight text-brand-700">Find Campus & Experienced Jobs Faster</h1>
        <p className="mt-3 max-w-3xl text-slate-600">
          Aggregate jobs from multiple platforms and university channels, with normalized search filters and source attribution.
        </p>

        <form action="/jobs" className="mt-5 grid gap-2 md:max-w-2xl md:grid-cols-[1fr_auto]">
          <label className="sr-only" htmlFor="home-keyword">
            Search jobs by keyword
          </label>
          <input
            id="home-keyword"
            name="keyword"
            className="input"
            placeholder="Search by keyword, skill or role..."
          />
          <button type="submit" className="btn-primary">
            Search Jobs
          </button>
        </form>

        <div className="mt-3 flex flex-wrap gap-2">
          <Link href="/jobs" className="btn-secondary">
            Browse all jobs
          </Link>
          <Link href="/stats" className="btn-secondary">
            View source stats
          </Link>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <article className="card">
          <h2 className="text-lg font-bold">Popular Cities</h2>
          <div className="mt-3 flex flex-wrap gap-2">
            {HOT_CITIES.map((city) => (
              <Link key={city} href={`/jobs?city=${encodeURIComponent(city)}`} className="btn-secondary">
                {city}
              </Link>
            ))}
          </div>
        </article>

        <article className="card">
          <h2 className="text-lg font-bold">Popular Categories</h2>
          <div className="mt-3 flex flex-wrap gap-2">
            {HOT_CATEGORIES.map((category) => (
              <Link key={category} href={`/jobs?category=${encodeURIComponent(category)}`} className="btn-secondary">
                {category}
              </Link>
            ))}
          </div>
        </article>
      </section>

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-xl font-bold">Latest Jobs</h2>
          <Link href="/jobs" className="text-sm font-semibold text-brand-700 hover:underline">
            See all
          </Link>
        </div>
        <LatestJobs />
      </section>
    </div>
  );
}
