import { clsx, type ClassValue } from "clsx";

export function cn(...inputs: ClassValue[]): string {
  return clsx(inputs);
}

export function formatDate(iso?: string | null): string {
  if (!iso) {
    return "Unknown";
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
    return "Salary negotiable";
  }
  const unit = currency === "CNY" ? "¥" : `${currency} `;
  const suffix = period === "year" ? "/year" : "/month";
  return `${unit}${(min ?? 0).toLocaleString()} - ${(max ?? 0).toLocaleString()}${suffix}`;
}
