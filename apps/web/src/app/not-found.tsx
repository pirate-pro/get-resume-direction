import Link from "next/link";

export default function NotFoundPage(): JSX.Element {
  return (
    <div className="card text-center">
      <h1 className="text-2xl font-bold text-brand-700">Page not found</h1>
      <p className="mt-2 text-slate-600">The requested page does not exist.</p>
      <Link href="/" className="btn-primary mt-4 inline-flex">
        Back to home
      </Link>
    </div>
  );
}
