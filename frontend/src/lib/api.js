// src/lib/api.js
import { useEffect, useState } from "react";
import { ls } from "./ls";

// ---------- API base (editable, persisted) ----------
export function useApiBase() {
  const [apiBase, setApiBase] = useState(() =>
    // fallback order: LS -> .env -> "/api"
    (ls.get("apiBase", process.env.REACT_APP_API_BASE || "/api") || "/api")
  );
  useEffect(() => { ls.set("apiBase", apiBase); }, [apiBase]);
  return { apiBase: normalizeBase(apiBase), setApiBase };
}

function normalizeBase(b) {
  // remove trailing slash only; keep scheme/host
  return String(b || "/api").replace(/\/$/, "");
}

// Join base + path correctly whether you pass "/movies" or "movies/"
export function apiUrl(apiBase, path, params) {
  const base = normalizeBase(apiBase);
  const p = String(path || "").replace(/^\//, ""); // strip leading slash
  const url = `${base}/${p}`;                       // exactly one slash between
  if (!params) return url;
  const qs = new URLSearchParams(params);
  return `${url}?${qs.toString()}`;
}

// ---------- Fetch with nice errors ----------
export async function fetchJson(url, opts = {}) {
  const res = await fetch(url, { credentials: "include", ...opts });
  if (!res.ok) {
    let body = "";
    try { body = await res.text(); } catch {}
    throw new Error(`HTTP ${res.status} @ ${url}\n${body.slice(0, 300)}`);
  }
  return res.json();
}
