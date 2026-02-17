import { StatsBoard } from "@/features/stats/components/stats-board";

export default function StatsPage(): JSX.Element {
  return (
    <div className="space-y-4">
      <header>
        <h1 className="text-2xl font-black text-brand-700">来源与统计</h1>
        <p className="text-sm text-slate-600">展示职位与校园活动的来源、城市、类别和学校聚合数量。</p>
      </header>
      <StatsBoard />
    </div>
  );
}
