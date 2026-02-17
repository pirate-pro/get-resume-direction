export function LoadingState({ label = "加载中..." }: { label?: string }): JSX.Element {
  return (
    <div className="card animate-pulse">
      <p className="text-sm text-slate-600">{label}</p>
    </div>
  );
}
