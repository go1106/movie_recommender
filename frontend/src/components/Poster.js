export default function Poster({ src, alt, className = "" }) {
  const ph = "data:image/svg+xml;utf8," + encodeURIComponent(
    `<svg xmlns='http://www.w3.org/2000/svg' width='300' height='450'><rect width='100%' height='100%' fill='#111'/><text x='50%' y='50%' fill='#888' font-size='20' text-anchor='middle' dominant-baseline='middle'>No Poster</text></svg>`
  );
  return <img src={src || ph} alt={alt} className={className} />;
}