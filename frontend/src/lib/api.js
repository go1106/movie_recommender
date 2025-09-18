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

