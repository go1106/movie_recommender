import { useState } from "react";
import { getToken, authFetchJson } from "../lib/api";
import Card from "./Card";


export default function MovieActions({ apiBase, movieId, onChanged }) {
  const authed = !!localStorage.getItem("token");

  const [score, setScore] = useState("4.5"); // string to allow 0.5 steps
  const [tag, setTag] = useState("");
  const [comment, setComment] = useState("");

  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  async function postRating(e) {
    e.preventDefault();
    if (!authed) return alert("Please sign in to rate.");
    setBusy(true); setMsg(""); setErr("");
    try {
      await authFetchJson(`${apiBase}/ratings/`, {
        method: "POST",
        body: JSON.stringify({ movie: movieId, rating: Number(score) }),
      });
      setMsg("Rating saved.");
      onChanged?.();               // refresh Movie details (avg/count)
    } catch (e) {
      setErr(String(e));
    } finally { setBusy(false); }
  }

  async function postTag(e) {
    e.preventDefault();
    if (!authed) return alert("Please sign in to tag.");
    if (!tag.trim()) return;
    setBusy(true); setMsg(""); setErr("");
    try {
      await authFetchJson(`${apiBase}/taggings/`, {
        method: "POST",
        body: JSON.stringify({ movie: movieId, tag_name: tag.trim() }),
      });
      setMsg("Tag added.");
      setTag("");
      onChanged?.();
    } catch (e) {
      setErr(String(e));
    } finally { setBusy(false); }
  }

  async function postComment(e) {
    e.preventDefault();
    if (!authed) return alert("Please sign in to comment.");
    if (!comment.trim()) return;
    setBusy(true); setMsg(""); setErr("");
    try {
      await authFetchJson(`${apiBase}/comments/`, {
        method: "POST",
        body: JSON.stringify({ movie: movieId, text: comment.trim() }),
      });
      setMsg("Comment posted.");
      setComment("");
      onChanged?.();
    } catch (e) {
      setErr(String(e));
    } finally { setBusy(false); }
  }

  return (
    <Card className="p-4">
     

      {!authed && (
        <div className="mb-3 rounded-lg border border-yellow-400/40 bg-yellow-50/90 p-2 text-xs text-yellow-900">
          Sign in to rate, tag, or comment.
      
        </div>
      )}

      <form onSubmit={postRating} className="mb-3 flex flex-wrap items-center gap-2">
        <label className="text-sm text-zinc-300">Rate:</label>
        <input
          type="number" step="0.5" min="0" max="5"
          value={score} onChange={(e) => setScore(e.target.value)}
          className="w-24 rounded-xl border border-zinc-700 bg-zinc-900 px-2 py-1 text-zinc-100"
          disabled={!authed || busy}
        />
        <button className="rounded-xl bg-indigo-600 px-3 py-1.5 text-sm text-white hover:bg-indigo-500 disabled:opacity-50"
                disabled={!authed || busy}>Save rating</button>
      </form>

      <form onSubmit={postTag} className="mb-3 flex flex-wrap items-center gap-2">
        <label className="text-sm text-zinc-300">Tag:</label>
        <input
          value={tag} onChange={(e) => setTag(e.target.value)} placeholder="e.g. classic"
          className="rounded-xl border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-zinc-100"
          disabled={!authed || busy}
        />
        <button className="rounded-xl bg-zinc-800 px-3 py-1.5 text-sm text-white hover:bg-zinc-700 disabled:opacity-50"
                disabled={!authed || busy}>Add tag</button>
      </form>

      <form onSubmit={postComment} className="flex flex-col gap-2">
        <label className="text-sm text-zinc-300">Comment:</label>
        <textarea
          rows={3}
          value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Write a comment…"
          className="rounded-xl border border-zinc-700 bg-zinc-900 px-3 py-2 text-zinc-100"
          disabled={!authed || busy}
        />
        <div className="flex justify-end">
          <button className="rounded-xl bg-zinc-800 px-3 py-1.5 text-sm text-white hover:bg-zinc-700 disabled:opacity-50"
                  disabled={!authed || busy}>Post comment</button>
        </div>
      </form>

      {(msg || err) && (
        <div className="mt-3 text-xs">
          {msg && <span className="text-emerald-400">{msg}</span>}
          {err && <span className="text-red-400">{err}</span>}
        </div>
      )}
    </Card>
  );
}
