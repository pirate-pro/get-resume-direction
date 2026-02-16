export interface ApiResponse<T> {
  code: number;
  message: string;
  request_id?: string;
  data: T;
}

export class ApiError extends Error {
  status: number;
  code: number;
  payload?: unknown;

  constructor(message: string, status: number, code: number, payload?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.payload = payload;
  }
}
