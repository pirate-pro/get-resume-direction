"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { JobsQueryParams } from "@/types/jobs";

const schema = z.object({
  keyword: z.string().optional(),
  province: z.string().optional(),
  city: z.string().optional(),
  category: z.string().optional(),
  education: z.string().optional(),
  experience_min: z.string().optional(),
  salary_min: z.string().optional(),
  salary_max: z.string().optional(),
  sort_by: z.enum(["time", "salary", "relevance"]).default("time")
});

type FormValues = z.infer<typeof schema>;

interface JobsFilterFormProps {
  initial: JobsQueryParams;
  onApply: (next: JobsQueryParams) => void;
}

export function JobsFilterForm({ initial, onApply }: JobsFilterFormProps): JSX.Element {
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      keyword: initial.keyword ?? "",
      province: initial.province ?? "",
      city: initial.city ?? "",
      category: initial.category ?? "",
      education: initial.education ?? "",
      experience_min: initial.experience_min ? String(initial.experience_min) : "",
      salary_min: initial.salary_min ? String(initial.salary_min) : "",
      salary_max: initial.salary_max ? String(initial.salary_max) : "",
      sort_by: initial.sort_by ?? "time"
    }
  });

  const submit = form.handleSubmit((values) => {
    onApply({
      ...initial,
      page: 1,
      keyword: values.keyword || undefined,
      province: values.province || undefined,
      city: values.city || undefined,
      category: values.category || undefined,
      education: values.education || undefined,
      experience_min: values.experience_min ? Number(values.experience_min) : undefined,
      salary_min: values.salary_min ? Number(values.salary_min) : undefined,
      salary_max: values.salary_max ? Number(values.salary_max) : undefined,
      sort_by: values.sort_by
    });
  });

  return (
    <form className="card grid gap-3 md:grid-cols-4" onSubmit={submit}>
      <label className="md:col-span-2">
        <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">Keyword</span>
        <input className="input" placeholder="FastAPI / Data Engineer" {...form.register("keyword")} />
      </label>
      <label>
        <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">Province</span>
        <input className="input" placeholder="Guangdong" {...form.register("province")} />
      </label>
      <label>
        <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">City</span>
        <input className="input" placeholder="Shenzhen" {...form.register("city")} />
      </label>
      <label>
        <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">Category</span>
        <input className="input" placeholder="Backend Engineering" {...form.register("category")} />
      </label>
      <label>
        <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">Education</span>
        <select className="select" {...form.register("education")}>
          <option value="">All</option>
          <option value="unknown">Unknown</option>
          <option value="college">College</option>
          <option value="bachelor">Bachelor</option>
          <option value="master">Master</option>
          <option value="phd">PhD</option>
        </select>
      </label>
      <label>
        <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">Exp (months)</span>
        <input className="input" inputMode="numeric" placeholder="12" {...form.register("experience_min")} />
      </label>
      <label>
        <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">Salary Min</span>
        <input className="input" inputMode="numeric" placeholder="15000" {...form.register("salary_min")} />
      </label>
      <label>
        <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">Salary Max</span>
        <input className="input" inputMode="numeric" placeholder="50000" {...form.register("salary_max")} />
      </label>
      <label>
        <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">Sort</span>
        <select className="select" {...form.register("sort_by")}>
          <option value="time">Newest</option>
          <option value="salary">Salary</option>
          <option value="relevance">Relevance</option>
        </select>
      </label>
      <div className="flex items-end gap-2 md:col-span-2">
        <button type="submit" className="btn-primary">
          Apply Filters
        </button>
        <button
          type="button"
          className="btn-secondary"
          onClick={() => {
            form.reset({ sort_by: "time" });
            onApply({ page: 1, page_size: initial.page_size ?? 20, sort_by: "time" });
          }}
        >
          Reset
        </button>
      </div>
    </form>
  );
}
