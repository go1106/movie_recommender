// src/pages/SignUp.jsx
import { fetchJson } from "../lib/api";
import { useState } from "react";
export default function SignUp({ apiBase, onDone }) {
  const [u,setU]=useState(""); const [e,setE]=useState(""); const [p,setP]=useState("");
  const [err,setErr]=useState("");
  async function submit(evn){ evn.preventDefault();
    try{
      await fetchJson(`${apiBase}/auth/register/`, { method:"POST", body: JSON.stringify({ username:u, email:e, password:p }) });
      onDone?.();
    }catch(e){ setErr(String(e)); }
  }
  return (<form onSubmit={submit} className="grid gap-2 max-w-sm mx-auto">
    <input value={u} onChange={e=>setU(e.target.value)} placeholder="username" />
    <input value={e} onChange={e=>setE(e.target.value)} placeholder="email" />
    <input type="password" value={p} onChange={e=>setP(e.target.value)} placeholder="password" />
    <button>Create account</button>
    {err && <div className="text-red-500 text-sm">{err}</div>}
  </form>);
}
