import { useState } from "react";
import  { Link }  from "react-router-dom";
import  Button  from "./Button";
import  Input  from "./Input";


/**
 * Shell.jsx — app layout wrapper (updated)
 *
 * What changed:
 * 1) Added visual override props so pages can control background/text easily.
 * 2) Kept your API Base popover.
 *
 * Props
 * - children
 * - apiBase, setApiBase
 * - variant: "gradient" | "dark" | "light"  (default: "gradient")
 * - shellClassName: extra classes on outer wrapper (lets you force !bg-black, etc.)
 * - mainClassName: extra classes on <main>
 * - maxWidth: container width class (default: "max-w-6xl")
 */

function cx(...xs) { return xs.filter(Boolean).join(" "); }

export default function Shell({
  children,
  apiBase,
  setApiBase,
  variant = "gradient",
  shellClassName = "",
  mainClassName = "",
  maxWidth = "max-w-6xl",
}) {
  const [showCfg, setShowCfg] = useState(false);

  const variantRoot =
    variant === "dark"
      ? "min-h-screen bg-black text-white"
      : variant === "light"
      ? "min-h-screen bg-white text-zinc-900"
      : // gradient (default)
        "min-h-screen bg-gradient-to-b from-zinc-950 to-zinc-900 text-zinc-100";

  const headerBg =
    variant === "light"
      ? "bg-white/80 supports-[backdrop-filter]:bg-white/60 border-zinc-200"
      : "bg-zinc-950/80 supports-[backdrop-filter]:bg-zinc-950/60 border-zinc-800/70";

  return (
    <div className={cx(variantRoot, shellClassName)}>
      <header className={cx("sticky top-0 z-20 border-b backdrop-blur", headerBg)}>
        <div className={cx("mx-auto flex items-center justify-between px-4 py-3", maxWidth)}>
          <nav className="flex items-center gap-3 text-sm">
            <Link className="rounded-xl px-2 py-1 hover:bg-zinc-800/60" to="/">Home</Link>
            <Link className="rounded-xl px-2 py-1 hover:bg-zinc-800/60" to="/browse">Browse</Link>
            <Link className="rounded-xl px-2 py-1 hover:bg-zinc-800/60" to="/trending">Trending</Link>
            <Link className="rounded-xl px-2 py-1 hover:bg-zinc-800/60" to="/top-rated">Top Rated</Link>
            <Link className="rounded-xl px-2 py-1 hover:bg-zinc-800/60" to="/recs">Recs</Link>
          </nav>
          <div className="flex items-center gap-2">
          
          </div>
        </div>
        {showCfg && (
          <div className={cx("mx-auto px-4 pb-3", maxWidth)}>
            <div className="flex items-center gap-2">
              <label className="text-xs text-zinc-400">API Base</label>
              <input
                value={apiBase}
                onChange={(e) => setApiBase?.(e.target.value)}
                className={cx(
                  "w-[360px] rounded-md border px-2 py-1 text-sm",
                  variant === "light" ? "bg-white text-zinc-900" : "bg-zinc-900 text-zinc-100 border-zinc-700"
                )}
              />
              <button
                type="button"
                className="rounded-md border px-3 py-1 text-sm hover:bg-white/10"
                onClick={() => setShowCfg(false)}
              >
                Close
              </button>
            </div>
            <p className="mt-1 text-xs text-zinc-500">e.g. http://127.0.0.1:8000/api</p>
          </div>
        )}
      </header>

      <main className={cx("mx-auto px-4 py-6", maxWidth, mainClassName)}>
        {children}
      </main>
    </div>
  );
}

/**
 * Examples
 *
 * // Default (gradient)
 * <Shell apiBase={api} setApiBase={setApi}>
 *   <Page />
 * </Shell>
 *
 * // Force dark page (black bg, white text)
 * <Shell apiBase={api} setApiBase={setApi} variant="dark">
 *   <Page />
 * </Shell>
 *
 * // Custom overrides additionally
 * <Shell variant="dark" shellClassName="!bg-black !text-white" mainClassName="!bg-black">
 *   <Page />
 * </Shell>
 */


