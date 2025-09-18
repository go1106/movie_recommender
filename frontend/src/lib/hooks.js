import { useState, useEffect } from "react";
export const ls = {
  get(key, fallback) {
    try { const v = localStorage.getItem(key); return v ?? fallback; } catch { return fallback; }
  },
  set(key, val) { try { localStorage.setItem(key, val); } catch {} }
};

export function useDebounce(value, delay = 400) {
  const [v, setV] = useState(value);
  useEffect(() => { const t = setTimeout(() => setV(value), delay); return () => clearTimeout(t); }, [value, delay]);
  return v;
}

