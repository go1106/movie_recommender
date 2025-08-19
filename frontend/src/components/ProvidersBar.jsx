// src/components/ProvidersBar.jsx
const IMG_BASE = "https://image.tmdb.org/t/p/w92";

export default function ProvidersBar({ providers = [], region = "US" }) {
  const inRegion = providers.filter(p => p.region === region.toUpperCase());
  if (!inRegion.length) return null;

  // group by type
  const groups = inRegion.reduce((acc, p) => {
    (acc[p.type] ||= []).push(p.provider);
    return acc;
  }, {});

  const order = ["flatrate", "free", "ads", "rent", "buy"]; // display order

  return (
    <div className="mt-3 space-y-2">
      {order.map(type => groups[type] && (
        <div key={type} className="flex items-center gap-2">
          <div className="text-xs w-16 capitalize text-neutral-600">{type}</div>
          <div className="flex gap-2 flex-wrap">
            {groups[type].sort((a,b)=>(a.display_priority||999)-(b.display_priority||999)).map(p => (
              <div key={p.tmdb_id} className="flex items-center gap-1 px-2 py-1 rounded-full bg-neutral-100">
                {p.logo_path && <img src={`${IMG_BASE}${p.logo_path}`} alt={p.name} className="w-5 h-5 rounded" loading="lazy" />}
                <span className="text-xs">{p.name}</span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
