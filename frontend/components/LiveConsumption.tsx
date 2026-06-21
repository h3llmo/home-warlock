"use client";
import useSWR from "swr";

const fetcher = (url: string) => fetch(url).then((r) => r.json());

function WattsBar({ label, watts, total }: { label: string; watts: number; total: number }) {
  const pct = total > 0 ? (watts / total) * 100 : 0;
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span className="text-slate-400">{label}</span>
        <span className="text-slate-200 font-medium tabular-nums">{watts.toLocaleString("fr-BE")} W</span>
      </div>
      <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
        <div className="h-full bg-blue-500 rounded-full transition-all duration-500" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export default function LiveConsumption() {
  const backend = process.env.NEXT_PUBLIC_BACKEND_URL;
  const { data, error } = useSWR(`${backend}/api/realtime`, fetcher, { refreshInterval: 10000 });

  if (error) return <Card><p className="text-red-400 text-sm">Erreur</p></Card>;
  if (!data) return <Card><p className="text-slate-500 text-sm animate-pulse">Chargement...</p></Card>;

  const total = data.watts_total as number;
  const voiture = data.watts_voiture as number;
  const maison = data.watts_maison as number;

  return (
    <Card>
      <div className="text-3xl font-bold tabular-nums mb-4">
        {total.toLocaleString("fr-BE")} <span className="text-lg font-normal text-slate-400">W</span>
      </div>
      <div className="space-y-3">
        <WattsBar label="Voiture ⚡" watts={voiture} total={total} />
        <WattsBar label="Maison 🏠" watts={maison} total={total} />
      </div>
    </Card>
  );
}

function Card({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-slate-900 rounded-2xl p-5 border border-slate-800 shadow-lg">
      <h2 className="text-xs font-semibold uppercase tracking-widest text-slate-500 mb-3">Consommation live</h2>
      {children}
    </div>
  );
}
