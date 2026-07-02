import { render, screen } from "@testing-library/react";
import { beforeEach, expect, test, vi } from "vitest";
import App from "./App";

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string) => {
      if (url === "/api/health") {
        return Promise.resolve({ json: () => Promise.resolve({ status: "ok" }) });
      }
      return Promise.resolve({ json: () => Promise.resolve({ accounts: [] }) });
    }),
  );
});

test("renders the app heading", () => {
  render(<App />);
  expect(screen.getByRole("heading", { name: "Ignite" })).toBeInTheDocument();
});
