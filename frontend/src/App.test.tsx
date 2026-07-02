import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, expect, test, vi } from "vitest";
import App from "./App";

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn(() => Promise.resolve({ json: () => Promise.resolve({ status: "ok" }) })),
  );
});

test("renders brand and nav links", () => {
  render(
    <MemoryRouter>
      <App />
    </MemoryRouter>,
  );
  expect(screen.getByRole("heading", { name: "Ignite" })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: /Budget/ })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: /Investments/ })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: /FIRE/ })).toBeInTheDocument();
});

test("default route lands on the Budget page", () => {
  render(
    <MemoryRouter initialEntries={["/"]}>
      <App />
    </MemoryRouter>,
  );
  expect(screen.getByRole("heading", { name: "Budget" })).toBeInTheDocument();
});
