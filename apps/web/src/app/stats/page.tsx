import { StatsBoard } from "@/features/stats/components/stats-board";

export default function StatsPage(): JSX.Element {
  return (
    <div className="space-y-4">
      <header>
        <h1 className="text-2xl font-black text-brand-700">Sources & Stats</h1>
        <p className="text-sm text-slate-600">Operations dashboard with source, city and category counts.</p>
      </header>
      <StatsBoard />
    </div>
  );
}
