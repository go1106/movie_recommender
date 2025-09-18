export default function Input({ className = "", ...props }) {
  return <input className={`w-full rounded-xl border border-zinc-700 bg-zinc-900 px-3 py-2 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-indigo-600 ${className}`} {...props} />
}