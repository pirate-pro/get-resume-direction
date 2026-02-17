export function ErrorState({ message, retry }: { message: string; retry?: () => void }): JSX.Element {
  return (
    <div className="card border-red-200 bg-red-50">
      <h3 className="text-base font-semibold text-red-700">请求失败</h3>
      <p className="mt-2 text-sm text-red-600">{message}</p>
      {retry ? (
        <button type="button" onClick={retry} className="btn-secondary mt-3">
          重试
        </button>
      ) : null}
    </div>
  );
}
