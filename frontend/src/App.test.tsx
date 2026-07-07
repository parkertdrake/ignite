import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, expect, test, vi } from "vitest";
import App from "./App";

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => ({
      ok: true,
      status: 200,
      json: async () =>
        String(url).includes("/api/budgets") ? [] : { status: "ok" },
    })),
  );
});

function renderApp(initialEntries: string[] = ["/"]) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={initialEntries}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

test("renders brand and nav links", () => {
  renderApp();
  // Sidebar defaults collapsed, so the brand renders in both the topbar and the
  // (hidden) sidebar header — assert at least one is present.
  expect(screen.getAllByRole("heading", { name: "Ignite" }).length).toBeGreaterThan(0);
  expect(screen.getByRole("link", { name: /Budget/ })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: /Investments/ })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: /FIRE/ })).toBeInTheDocument();
});

test("default route lands on the Budget page", () => {
  renderApp(["/"]);
  expect(screen.getByRole("heading", { name: "Budget" })).toBeInTheDocument();
});
