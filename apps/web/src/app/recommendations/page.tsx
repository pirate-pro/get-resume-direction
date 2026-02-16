import { mockRecommendations } from "@/mocks/recommendations";

export default function RecommendationsPage(): JSX.Element {
  return (
    <div className="space-y-4">
      <header>
        <h1 className="text-2xl font-black text-brand-700">Recommendations (Phase 2 Placeholder)</h1>
        <p className="text-sm text-slate-600">
          This route defines expected data shapes and recommendation explanation area for future backend integration.
        </p>
      </header>

      <section className="grid gap-3">
        {mockRecommendations.map((item) => (
          <article key={item.id} className="card">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h2 className="text-lg font-bold text-brand-700">{item.title}</h2>
                <p className="text-sm text-slate-600">
                  {item.company_name} · {item.city}
                </p>
              </div>
              <span className="rounded-md bg-brand-100 px-2 py-1 text-xs font-semibold text-brand-700">
                score {Math.round(item.score * 100)}
              </span>
            </div>
            <div className="mt-3 rounded-md border border-brand-100 bg-brand-50 p-3">
              <h3 className="text-sm font-semibold">Recommendation reason</h3>
              <p className="mt-1 text-sm text-slate-700">{item.reason}</p>
            </div>
          </article>
        ))}
      </section>
    </div>
  );
}
