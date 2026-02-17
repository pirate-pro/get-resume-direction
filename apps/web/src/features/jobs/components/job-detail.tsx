"use client";

import { ErrorState } from "@/components/states/error-state";
import { LoadingState } from "@/components/states/loading-state";
import { formatDate, formatSalary } from "@/lib/utils";
import { JobDetail } from "@/types/jobs";

import { useJobDetail } from "../hooks/use-job-detail";

interface JobDetailProps {
  jobId: number;
  initialData?: JobDetail;
}

export function JobDetailSection({ jobId, initialData }: JobDetailProps): JSX.Element {
  const query = useJobDetail(jobId, initialData);

  if (query.isLoading) {
    return <LoadingState label="职位详情加载中..." />;
  }

  if (query.isError) {
    return <ErrorState message={query.error.message} retry={() => query.refetch()} />;
  }

  if (!query.data) {
    return <ErrorState message="职位详情不可用" />;
  }

  const job = query.data;

  return (
    <article className="space-y-4">
      <section className="card">
        <h1 className="text-2xl font-bold text-brand-700">{job.title}</h1>
        <p className="mt-1 text-sm text-slate-600">
          {job.company_name} · {job.city || "未知城市"}
        </p>
        <p className="mt-2 text-base font-semibold text-slate-800">
          {formatSalary(job.salary_min, job.salary_max, job.salary_currency || "CNY", job.salary_period || "month")}
        </p>
        <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-600">
          <span className="rounded-full bg-brand-50 px-3 py-1">学历: {job.education_requirement || "未知"}</span>
          <span className="rounded-full bg-brand-50 px-3 py-1">来源: {job.source_code}</span>
          <span className="rounded-full bg-brand-50 px-3 py-1">发布时间: {formatDate(job.published_at)}</span>
        </div>
        <a
          href={job.source_url}
          target="_blank"
          rel="noopener noreferrer nofollow"
          className="btn-primary mt-4"
          aria-label="前往原站查看并投递"
        >
          去原站查看 / 投递
        </a>
      </section>

      <section className="card space-y-4">
        <div>
          <h2 className="text-lg font-semibold">岗位职责</h2>
          <p className="mt-1 whitespace-pre-wrap text-sm leading-6 text-slate-700">
            {job.responsibilities || "暂无"}
          </p>
        </div>
        <div>
          <h2 className="text-lg font-semibold">任职要求</h2>
          <p className="mt-1 whitespace-pre-wrap text-sm leading-6 text-slate-700">
            {job.qualifications || "暂无"}
          </p>
        </div>
        <div>
          <h2 className="text-lg font-semibold">福利标签</h2>
          <p className="mt-1 text-sm text-slate-700">{job.benefits?.join(" · ") || "暂无"}</p>
        </div>
      </section>
    </article>
  );
}
