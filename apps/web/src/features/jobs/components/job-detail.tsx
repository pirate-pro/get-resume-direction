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
    return <LoadingState label="Loading job detail..." />;
  }

  if (query.isError) {
    return <ErrorState message={query.error.message} retry={() => query.refetch()} />;
  }

  if (!query.data) {
    return <ErrorState message="Job detail unavailable" />;
  }

  const job = query.data;

  return (
    <article className="space-y-4">
      <section className="card">
        <h1 className="text-2xl font-bold text-brand-700">{job.title}</h1>
        <p className="mt-1 text-sm text-slate-600">
          {job.company_name} · {job.city || "Unknown city"}
        </p>
        <p className="mt-2 text-base font-semibold text-slate-800">
          {formatSalary(job.salary_min, job.salary_max, job.salary_currency || "CNY", job.salary_period || "month")}
        </p>
        <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-600">
          <span className="rounded-full bg-brand-50 px-3 py-1">Education: {job.education_requirement || "Unknown"}</span>
          <span className="rounded-full bg-brand-50 px-3 py-1">Source: {job.source_code}</span>
          <span className="rounded-full bg-brand-50 px-3 py-1">Published: {formatDate(job.published_at)}</span>
        </div>
        <a
          href={job.source_url}
          target="_blank"
          rel="noopener noreferrer nofollow"
          className="btn-primary mt-4"
          aria-label="View original source and apply"
        >
          View / Apply on source site
        </a>
      </section>

      <section className="card space-y-4">
        <div>
          <h2 className="text-lg font-semibold">Responsibilities</h2>
          <p className="mt-1 whitespace-pre-wrap text-sm leading-6 text-slate-700">
            {job.responsibilities || "Not provided"}
          </p>
        </div>
        <div>
          <h2 className="text-lg font-semibold">Qualifications</h2>
          <p className="mt-1 whitespace-pre-wrap text-sm leading-6 text-slate-700">
            {job.qualifications || "Not provided"}
          </p>
        </div>
        <div>
          <h2 className="text-lg font-semibold">Benefits</h2>
          <p className="mt-1 text-sm text-slate-700">{job.benefits?.join(" · ") || "Not provided"}</p>
        </div>
      </section>
    </article>
  );
}
