"use client";

export default function GlobalError({
  error,
  reset
}: {
  error: Error & { digest?: string };
  reset: () => void;
}): JSX.Element {
  return (
    <div className="card border-red-200">
      <h2 className="text-xl font-bold text-red-700">Application error</h2>
      <p className="mt-2 text-sm text-red-600">{error.message}</p>
      <button type="button" className="btn-primary mt-4" onClick={() => reset()}>
        Retry
      </button>
    </div>
  );
}
