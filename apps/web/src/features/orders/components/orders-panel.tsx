"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useSearchParams } from "next/navigation";
import { useMemo } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { EmptyState } from "@/components/states/empty-state";
import { ErrorState } from "@/components/states/error-state";
import { LoadingState } from "@/components/states/loading-state";
import { useOrders, useCreateOrder } from "@/features/orders/hooks/use-orders";
import { formatDate } from "@/lib/utils";
import { CreateOrderRequest } from "@/types/orders";

const schema = z.object({
  user_name: z.string().min(1, "请输入姓名"),
  phone: z.string().min(6, "请输入手机号"),
  wechat_id: z.string().optional(),
  school_name: z.string().optional(),
  major: z.string().optional(),
  graduation_year: z.string().optional(),
  resume_url: z.string().optional(),
  target_company_name: z.string().optional(),
  target_event_id: z.string().optional(),
  target_source_url: z.string().optional(),
  delivery_type: z.enum(["onsite_resume_delivery", "online_apply_guidance"]).default("onsite_resume_delivery"),
  quantity: z.string().optional(),
  note: z.string().optional()
});

type FormValues = z.infer<typeof schema>;

export function OrdersPanel(): JSX.Element {
  const searchParams = useSearchParams();
  const createMutation = useCreateOrder();

  const initEventId = searchParams.get("event_id") ?? "";
  const initCompany = searchParams.get("company") ?? "";
  const initSourceUrl = searchParams.get("source_url") ?? "";

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      user_name: "",
      phone: "",
      wechat_id: "",
      school_name: "",
      major: "",
      graduation_year: "",
      resume_url: "",
      target_company_name: initCompany,
      target_event_id: initEventId,
      target_source_url: initSourceUrl,
      delivery_type: "onsite_resume_delivery",
      quantity: "1",
      note: ""
    }
  });

  const phoneWatch = form.watch("phone");
  const ordersQuery = useOrders(
    useMemo(
      () => ({
        page: 1,
        page_size: 10,
        phone: phoneWatch && phoneWatch.length >= 6 ? phoneWatch : undefined
      }),
      [phoneWatch]
    )
  );

  const submit = form.handleSubmit(async (values) => {
    const payload: CreateOrderRequest = {
      user_name: values.user_name,
      phone: values.phone,
      wechat_id: values.wechat_id || undefined,
      school_name: values.school_name || undefined,
      major: values.major || undefined,
      graduation_year: values.graduation_year ? Number(values.graduation_year) : undefined,
      resume_url: values.resume_url || undefined,
      target_company_name: values.target_company_name || undefined,
      target_event_id: values.target_event_id ? Number(values.target_event_id) : undefined,
      target_source_url: values.target_source_url || undefined,
      delivery_type: values.delivery_type,
      quantity: values.quantity ? Number(values.quantity) : 1,
      note: values.note || undefined
    };
    await createMutation.mutateAsync(payload);
    form.reset({
      ...form.getValues(),
      note: ""
    });
  });

  return (
    <div className="grid gap-4 lg:grid-cols-[1.1fr_1fr]">
      <section className="card">
        <h2 className="text-lg font-bold text-brand-700">创建线下代投订单</h2>
        <p className="mt-1 text-sm text-slate-600">提交后会生成订单号，后续可接入支付与履约流程。</p>
        <form className="mt-4 grid gap-3 md:grid-cols-2" onSubmit={submit}>
          <label>
            <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">姓名</span>
            <input className="input" {...form.register("user_name")} />
          </label>
          <label>
            <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">手机号</span>
            <input className="input" {...form.register("phone")} />
          </label>
          <label>
            <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">微信号</span>
            <input className="input" {...form.register("wechat_id")} />
          </label>
          <label>
            <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">学校</span>
            <input className="input" {...form.register("school_name")} />
          </label>
          <label>
            <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">专业</span>
            <input className="input" {...form.register("major")} />
          </label>
          <label>
            <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">毕业年份</span>
            <input className="input" inputMode="numeric" {...form.register("graduation_year")} />
          </label>
          <label className="md:col-span-2">
            <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">简历链接（可选）</span>
            <input className="input" placeholder="https://..." {...form.register("resume_url")} />
          </label>
          <label>
            <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">目标活动 ID</span>
            <input className="input" inputMode="numeric" {...form.register("target_event_id")} />
          </label>
          <label>
            <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">目标公司</span>
            <input className="input" {...form.register("target_company_name")} />
          </label>
          <label className="md:col-span-2">
            <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">活动来源链接</span>
            <input className="input" placeholder="https://..." {...form.register("target_source_url")} />
          </label>
          <label>
            <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">服务类型</span>
            <select className="select" {...form.register("delivery_type")}>
              <option value="onsite_resume_delivery">线下代投</option>
              <option value="online_apply_guidance">网申辅导</option>
            </select>
          </label>
          <label>
            <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">数量</span>
            <input className="input" inputMode="numeric" {...form.register("quantity")} />
          </label>
          <label className="md:col-span-2">
            <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">备注</span>
            <textarea className="input h-24 py-2" {...form.register("note")} />
          </label>
          <div className="md:col-span-2">
            <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
              {createMutation.isPending ? "提交中..." : "提交订单"}
            </button>
          </div>
        </form>
      </section>

      <section className="card">
        <h2 className="text-lg font-bold text-brand-700">我的订单（手机号过滤）</h2>
        <p className="mt-1 text-sm text-slate-600">输入手机号后会自动拉取最近订单。</p>
        <div className="mt-4 space-y-3">
          {ordersQuery.isLoading ? <LoadingState label="订单加载中..." /> : null}
          {ordersQuery.isError ? <ErrorState message={ordersQuery.error.message} retry={() => ordersQuery.refetch()} /> : null}
          {!ordersQuery.isLoading && !ordersQuery.isError && ordersQuery.data ? (
            ordersQuery.data.items.length === 0 ? (
              <EmptyState title="暂无订单" description="提交第一笔订单后会在这里展示。" />
            ) : (
              ordersQuery.data.items.map((order) => (
                <article key={order.id} className="rounded-lg border border-brand-100 bg-brand-50/30 p-3">
                  <p className="text-sm font-semibold text-brand-700">{order.order_no}</p>
                  <p className="text-xs text-slate-600">
                    {order.user_name} · {order.phone}
                  </p>
                  <p className="text-xs text-slate-600">
                    状态: {order.status} · 类型: {order.delivery_type}
                  </p>
                  <p className="text-xs text-slate-500">创建时间: {formatDate(order.created_at)}</p>
                </article>
              ))
            )
          ) : null}
        </div>
      </section>
    </div>
  );
}
