// src/lib/api.js
import { useEffect, useState } from "react";
import { ls } from "./ls";

export function useApiBase() {
  const [apiBase, setApiBase] = useState(() => ls.get("apiBase", "http://127.0.0.1:8000/api"));
  useEffect(() => ls.set("apiBase", apiBase), [apiBase]);
  return { apiBase, setApiBase };
}

export async function fetchJson(url, opts) {
  const r = await fetch(url, opts);
  if (!r.ok) {
    const text = await r.text();
    throw new Error(`HTTP ${r.status}: ${text.slice(0, 300)}`);
  }
  return r.json();
}
// src/lib/api.js
export function getToken() { return localStorage.getItem("token") || ""; }

export async function ssfetchJson(url, opts={}) {
  const headers = new Headers(opts.headers || {});
  headers.set("Accept", "application/json");
  if (!headers.has("Content-Type") && opts.body) headers.set("Content-Type", "application/json");
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const res = await fetch(url, { ...opts, headers, credentials: "omit" });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  return res.json();
}
export function authFetchJson(url, opts = {}) {
  const token = localStorage.getItem("token") || "";
  const headers = new Headers(opts.headers || {});
  headers.set("Accept", "application/json");
  if (opts.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  return fetchJson(url, { ...opts, headers });
}



