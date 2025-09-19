// src/pages/SignIn.jsx
import { fetchJson } from "../lib/api";
import { useState } from "react";
export default function SignIn({ apiBase, onLogin }) {
  const [username, setU] = useState("demo");
  const [password, setP] = useState("demo");
  const [err, setErr] = useState("");
  async function submit(e){ e.preventDefault();
    try{
      const data = await fetchJson(`${apiBase}/auth/token/`, {
        method:"POST", body: JSON.stringify({ username, password })
      });
      localStorage.setItem("token", data.access);
      onLogin?.();
    }catch(e){ setErr(String(e)); }
  }
  return (<form onSubmit={submit} className="grid gap-2 max-w-sm mx-auto">
    <input value={username} onChange={e=>setU(e.target.value)} placeholder="username" />
    <input type="password" value={password} onChange={e=>setP(e.target.value)} placeholder="password" />
    <button>Sign in</button>
    {err && <div className="text-red-500 text-sm">{err}</div>}
  </form>);
}
