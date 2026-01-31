// Lightweight helper for local module execution through the backend preview.

export async function devPost<T>(path: string, body?: any, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json', ...(init?.headers || {}) },
    body: body != null ? JSON.stringify(body) : undefined,
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`POST ${path} failed: ${res.status} ${text}`);
  }
  return res.json();
}
