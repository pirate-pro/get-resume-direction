import Link from "next/link";

export default function NotFoundPage(): JSX.Element {
  return (
    <div className="card text-center">
      <h1 className="text-2xl font-bold text-brand-700">页面不存在</h1>
      <p className="mt-2 text-slate-600">你访问的页面不存在或已下线。</p>
      <Link href="/" className="btn-primary mt-4 inline-flex">
        返回首页
      </Link>
    </div>
  );
}
