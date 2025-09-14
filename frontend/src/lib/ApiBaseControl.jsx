// src/components/ApiBaseControl.jsx
import React from "react";
import { useApiBase } from "../lib/api";

export default function ApiBaseControl() {
  const { apiBase, setApiBase } = useApiBase(); // if used here, lift to context (see note below)
  return (
    <form
      onSubmit={(e) => e.preventDefault()}
      className="flex items-center gap-2 text-xs"
      title="API base (persisted)"
    >
      <span>API:</span>
      <input
        value={apiBase}
        onChange={(e) => setApiBase(e.target.value)}
        className="rounded border px-2 py-1 bg-white/90 text-black"
        style={{ width: 260 }}
      />
    </form>
  );
}
