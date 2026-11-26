
import { render, screen, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, expect, it } from "vitest";
import UploadPanel from "./UploadPanel";
import { waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { uploadReport } from "../api/reports";
import { useUIStore } from "../stores/uiStore";

vi.mock("../api/reports", () => ({
  uploadReport: vi.fn(),
}));

describe("UploadPanel", () => {
  it("displays the selected filename", () => {
    const client = new QueryClient();

    render(
      <QueryClientProvider client={client}>
        <UploadPanel />
      </QueryClientProvider>
    );

    const file = new File(["name,amount"], "sales.csv", {
      type: "text/csv",
    });

    const input = document.querySelector('input[type="file"]')!;

    fireEvent.change(input, {
      target: { files: [file] },
    });

    expect(screen.getByText("Selected: sales.csv")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Upload" })).toBeEnabled();
  });

  it("uploads the selected file and closes the panel on success", async () => {
    const file = new File(["name,amount"], "sales.csv", {
      type: "text/csv",
    });

    const closeUploadPanel = vi.fn();
    useUIStore.setState({ closeUploadPanel });

    vi.mocked(uploadReport).mockResolvedValue({} as never);

    const client = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    render(
      <QueryClientProvider client={client}>
        <UploadPanel />
      </QueryClientProvider>
    );

    fireEvent.change(document.querySelector('input[type="file"]')!, {
      target: { files: [file] },
    });

    fireEvent.click(screen.getByRole("button", { name: "Upload" }));

    await waitFor(() => {
      expect(uploadReport).toHaveBeenCalled();
      expect(vi.mocked(uploadReport).mock.calls[0][0]).toBe(file);
      expect(closeUploadPanel).toHaveBeenCalled();
    });
  });

  it("displays an error when the upload fails", async () => {
    const file = new File(["name,amount"], "sales.csv", {
      type: "text/csv",
    });

    vi.mocked(uploadReport).mockRejectedValue(
      new Error("Network error")
    );

    const client = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });

    render(
      <QueryClientProvider client={client}>
        <UploadPanel />
      </QueryClientProvider>
    );

    fireEvent.change(document.querySelector('input[type="file"]')!, {
      target: { files: [file] },
    });

    fireEvent.click(screen.getByRole("button", { name: "Upload" }));

    expect(
      await screen.findByRole("alert")
    ).toHaveTextContent("Upload failed. Please try again.");
  });
});
