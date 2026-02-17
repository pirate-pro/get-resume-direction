"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { EventsQueryParams } from "@/types/events";

const schema = z.object({
  keyword: z.string().optional(),
  city: z.string().optional(),
  school: z.string().optional(),
  company: z.string().optional(),
  event_type: z.preprocess(
    (value) => (value === "" ? undefined : value),
    z.enum(["talk", "job_fair", "interchoice", "company_event"]).optional()
  ),
  sort_by: z.enum(["time", "recent"]).default("time")
});

type FormValues = z.infer<typeof schema>;
const EVENT_TYPES: FormValues["event_type"][] = ["talk", "job_fair", "interchoice", "company_event"];

interface EventsFilterFormProps {
  initial: EventsQueryParams;
  onApply: (next: EventsQueryParams) => void;
}

export function EventsFilterForm({ initial, onApply }: EventsFilterFormProps): JSX.Element {
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      keyword: initial.keyword ?? "",
      city: initial.city ?? "",
      school: initial.school ?? "",
      company: initial.company ?? "",
      event_type: EVENT_TYPES.includes(initial.event_type as FormValues["event_type"])
        ? (initial.event_type as FormValues["event_type"])
        : undefined,
      sort_by: initial.sort_by ?? "time"
    }
  });

  const submit = form.handleSubmit((values) => {
    onApply({
      ...initial,
      page: 1,
      keyword: values.keyword || undefined,
      city: values.city || undefined,
      school: values.school || undefined,
      company: values.company || undefined,
      event_type: values.event_type || undefined,
      sort_by: values.sort_by
    });
  });

  return (
    <form className="card grid gap-3 md:grid-cols-4" onSubmit={submit}>
      <label className="md:col-span-2">
        <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">关键词</span>
        <input className="input" placeholder="公司 / 学校 / 宣讲会关键词" {...form.register("keyword")} />
      </label>
      <label>
        <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">城市</span>
        <input className="input" placeholder="深圳" {...form.register("city")} />
      </label>
      <label>
        <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">学校</span>
        <input className="input" placeholder="南方科技大学" {...form.register("school")} />
      </label>
      <label>
        <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">公司</span>
        <input className="input" placeholder="vivo" {...form.register("company")} />
      </label>
      <label>
        <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">活动类型</span>
        <select className="select" {...form.register("event_type")}>
          <option value="">全部</option>
          <option value="talk">宣讲会</option>
          <option value="job_fair">招聘会</option>
          <option value="interchoice">双选会</option>
          <option value="company_event">企业专场</option>
        </select>
      </label>
      <label>
        <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">排序</span>
        <select className="select" {...form.register("sort_by")}>
          <option value="time">按活动时间</option>
          <option value="recent">按收录时间</option>
        </select>
      </label>
      <div className="flex items-end gap-2 md:col-span-2">
        <button type="submit" className="btn-primary">
          应用筛选
        </button>
        <button
          type="button"
          className="btn-secondary"
          onClick={() => {
            form.reset({ sort_by: "time" });
            onApply({ page: 1, page_size: initial.page_size ?? 20, sort_by: "time" });
          }}
        >
          重置
        </button>
      </div>
    </form>
  );
}
