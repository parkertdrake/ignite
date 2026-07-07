// Minimal typed fetch wrapper. All calls go to the `/api` prefix, which
// Vite proxies to the backend in dev and the ingress routes in prod.
// (A full OpenAPI-generated client is the eventual goal — issue M0 #2.)

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

async function request<TResponse>(path: string, init?: RequestInit): Promise<TResponse> {
  const response = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      if (body?.detail) {
        detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
      }
    } catch {
      // response had no JSON body; fall back to statusText
    }
    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) {
    return undefined as TResponse;
  }
  return (await response.json()) as TResponse;
}

export const apiClient = {
  get: <TResponse>(path: string) => request<TResponse>(path),
  post: <TResponse>(path: string, body?: unknown) =>
    request<TResponse>(path, {
      method: "POST",
      body: body === undefined ? undefined : JSON.stringify(body),
    }),
  patch: <TResponse>(path: string, body?: unknown) =>
    request<TResponse>(path, {
      method: "PATCH",
      body: body === undefined ? undefined : JSON.stringify(body),
    }),
  del: <TResponse>(path: string) => request<TResponse>(path, { method: "DELETE" }),
};
