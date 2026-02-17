import { ApiError, ApiResponse } from "@/types/api";

const REQUEST_TIMEOUT_MS = 12000;

function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
}

function buildQueryString(params?: Record<string, string | number | undefined>): string {
  if (!params) {
    return "";
  }

  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === "") {
      return;
    }
    search.set(key, String(value));
  });
  const query = search.toString();
  return query ? `?${query}` : "";
}

export async function httpGet<T>(path: string, params?: Record<string, string | number | undefined>): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  const baseUrl = getApiBaseUrl().replace(/\/$/, "");
  const query = buildQueryString(params);
  const url = `${baseUrl}${path}${query}`;

  try {
    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json"
      },
      cache: "no-store",
      signal: controller.signal
    });

    const json = (await response.json()) as ApiResponse<T>;

    if (!response.ok || json.code !== 0) {
      throw new ApiError(json.message || "请求失败", response.status, json.code, json.data);
    }

    return json.data;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }

    throw new ApiError(
      error instanceof Error ? error.message : "网络异常",
      500,
      19999
    );
  } finally {
    clearTimeout(timeout);
  }
}

export async function httpPost<T, B extends object>(
  path: string,
  body: B
): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  const baseUrl = getApiBaseUrl().replace(/\/$/, "");
  const url = `${baseUrl}${path}`;

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(body),
      signal: controller.signal
    });

    const json = (await response.json()) as ApiResponse<T>;

    if (!response.ok || json.code !== 0) {
      throw new ApiError(json.message || "请求失败", response.status, json.code, json.data);
    }

    return json.data;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(error instanceof Error ? error.message : "网络异常", 500, 19999);
  } finally {
    clearTimeout(timeout);
  }
}
