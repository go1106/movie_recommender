export default function StarBar({ value = 0, size = 14 }) {
  // value: 0..5 (one decimal)
  const full = Math.floor(value);
  const half = value - full >= 0.5;
  const empty = 5 - full - (half ? 1 : 0);
  const star = (ch, i) => <span key={i} style={{ fontSize: size, lineHeight: 1 }}>{ch}</span>;
  return (
    <span title={`${value.toFixed(1)} / 5`} className="inline-flex items-center gap-0.5">
      {[...Array(full)].map((_, i) => star("★", `f${i}`))}
      {half && star("☆", "h")}
      {[...Array(empty)].map((_, i) => star("✩", `e${i}`))}
    </span>
  );
}