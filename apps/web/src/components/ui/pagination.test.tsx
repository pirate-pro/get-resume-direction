import { fireEvent, render, screen } from "@testing-library/react";

import { Pagination } from "./pagination";

describe("Pagination", () => {
  it("点击下一页会触发回调", () => {
    const onPageChange = vi.fn();

    render(<Pagination page={1} pageSize={20} total={120} onPageChange={onPageChange} />);
    fireEvent.click(screen.getByRole("button", { name: "下一页" }));

    expect(onPageChange).toHaveBeenCalledWith(2);
  });
});
