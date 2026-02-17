import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { JobDetailSection } from "@/features/jobs/components/job-detail";
import { ApiResponse } from "@/types/api";
import { JobDetail } from "@/types/jobs";

interface JobDetailPageProps {
  params: { id: string };
}

const REVALIDATE_SECONDS = 300;

async function fetchJobDetailServer(jobId: number): Promise<JobDetail | null> {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  const res = await fetch(`${base.replace(/\/$/, "")}/api/v1/jobs/${jobId}`, {
    next: { revalidate: REVALIDATE_SECONDS }
  });

  if (!res.ok) {
    return null;
  }

  const payload = (await res.json()) as ApiResponse<JobDetail>;
  if (payload.code !== 0) {
    return null;
  }
  return payload.data;
}

export async function generateMetadata({ params }: JobDetailPageProps): Promise<Metadata> {
  const jobId = Number(params.id);
  if (Number.isNaN(jobId)) {
    return { title: "职位详情" };
  }

  const detail = await fetchJobDetailServer(jobId);
  if (!detail) {
    return {
      title: "职位详情",
      description: "职位详情页"
    };
  }

  const title = `${detail.title} | ${detail.company_name}${detail.city ? ` | ${detail.city}` : ""}`;

  return {
    title,
    description: `${detail.company_name} 的 ${detail.title} 职位详情，来源：${detail.source_code}。`,
    alternates: {
      canonical: `/jobs/${jobId}`
    }
  };
}

export default async function JobDetailPage({ params }: JobDetailPageProps): Promise<JSX.Element> {
  const jobId = Number(params.id);
  if (Number.isNaN(jobId)) {
    notFound();
  }

  const detail = await fetchJobDetailServer(jobId);
  if (!detail) {
    notFound();
  }

  return (
    <div className="space-y-4">
      <JobDetailSection jobId={jobId} initialData={detail} />
    </div>
  );
}
