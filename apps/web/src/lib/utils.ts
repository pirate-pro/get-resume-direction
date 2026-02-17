import { clsx, type ClassValue } from "clsx";

export function cn(...inputs: ClassValue[]): string {
  return clsx(inputs);
}

export function formatDate(iso?: string | null): string {
  if (!iso) {
    return "未知";
  }
  return new Date(iso).toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit"
  });
}

export function formatSalary(
  min?: number | null,
  max?: number | null,
  currency = "CNY",
  period = "month"
): string {
  if (!min && !max) {
    return "薪资面议";
  }
  const unit = currency === "CNY" ? "¥" : `${currency} `;
  const suffix = period === "year" ? "/年" : "/月";
  return `${unit}${(min ?? 0).toLocaleString()} - ${(max ?? 0).toLocaleString()}${suffix}`;
}
