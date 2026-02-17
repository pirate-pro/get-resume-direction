"use client";

interface PaginationProps {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
}

export function Pagination({ page, pageSize, total, onPageChange }: PaginationProps): JSX.Element {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div className="mt-4 flex items-center justify-between rounded-lg border border-brand-100 bg-white px-4 py-3">
      <span className="text-sm text-slate-600">
        第 {page} / {totalPages} 页，共 {total} 条
      </span>
      <div className="flex gap-2">
        <button
          type="button"
          className="btn-secondary"
          onClick={() => onPageChange(Math.max(1, page - 1))}
          disabled={page <= 1}
          aria-label="上一页"
        >
          上一页
        </button>
        <button
          type="button"
          className="btn-secondary"
          onClick={() => onPageChange(Math.min(totalPages, page + 1))}
          disabled={page >= totalPages}
          aria-label="下一页"
        >
          下一页
        </button>
      </div>
    </div>
  );
}
