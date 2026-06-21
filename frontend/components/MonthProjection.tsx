"use client";
import useSWR from "swr";

const fetcher = (url: string) => fetch(url).then((r) => r.json());

export default function MonthProjection() {
  const backend = process.env.NEXT_PUBLIC_BACKEND_URL;
  const { data, error } = useSWR(`${backend}/api/projection`, fetcher, { refreshInterval: 300000 });

  if (error) return <Card><p className="text-red-400 text-sm">Erreur</p></Card>;
  if (!data) return <Card><p className="text-slate-500 text-sm animate-pulse">Chargement...</p></Card>;

  const variation = data.variation_pct as number;
  const variationColor = variation < 0 ? "text-green-400" : "text-red-400";
  const variationSign = variation >= 0 ? "+" : "";

  return (
    <Card>
      <div className="flex justify-between items-start">
        <div>
          <div className="text-slate-400 text-sm">Consommé ce mois</div>
          <div className="text-2xl font-bold mt-0.5">{(data.cout_mois_actuel as number).toFixed(2)} €</div>
        </div>
        <div className="text-right">
          <div className="text-slate-400 text-sm">Projeté</div>
          <div className="text-2xl font-bold mt-0.5">{(data.cout_projete as number).toFixed(2)} €</div>
        </div>
      </div>
      <div className={`mt-3 text-sm font-semibold ${variationColor}`}>
        {variationSign}{variation.toFixed(1)}% vs mois dernier ({(data.cout_mois_precedent as number).toFixed(2)} €)
      </div>
    </Card>
  );
}

function Card({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-slate-900 rounded-2xl p-5 border border-slate-800 shadow-lg">
      <h2 className="text-xs font-semibold uppercase tracking-widest text-slate-500 mb-3">Mois en cours</h2>
      {children}
    </div>
  );
}
