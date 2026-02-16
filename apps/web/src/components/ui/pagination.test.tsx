import { fireEvent, render, screen } from "@testing-library/react";

import { Pagination } from "./pagination";

describe("Pagination", () => {
  it("triggers next page callback", () => {
    const onPageChange = vi.fn();

    render(<Pagination page={1} pageSize={20} total={120} onPageChange={onPageChange} />);
    fireEvent.click(screen.getByRole("button", { name: "Next page" }));

    expect(onPageChange).toHaveBeenCalledWith(2);
  });
});
