export default function Button({ className = "", variant = "primary", ...props }) {
  const base = "inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium transition";
  const styles = variant === "ghost" ? "bg-transparent hover:bg-zinc-800 text-zinc-200" :
                 variant === "secondary" ? "bg-zinc-800 hover:bg-zinc-700 text-zinc-100" :
                 "bg-indigo-600 hover:bg-indigo-500 text-white";
  return <button className={`${base} ${styles} ${className}`} {...props} />
}