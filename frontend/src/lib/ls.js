// src/lib/ls.js
export const ls = {
  get(key, fallback) {
    try { const v = localStorage.getItem(key); return v ?? fallback; } catch { return fallback; }
  },
  set(key, value) {
    try { localStorage.setItem(key, value); } catch {}
  }
};
