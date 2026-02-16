export function EmptyState({ title, description }: { title: string; description: string }): JSX.Element {
  return (
    <div className="card text-center">
      <h3 className="text-base font-semibold text-slate-800">{title}</h3>
      <p className="mt-2 text-sm text-slate-600">{description}</p>
    </div>
  );
}
