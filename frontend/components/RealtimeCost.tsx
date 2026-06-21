"use client";
import useSWR from "swr";

const fetcher = (url: string) => fetch(url).then((r) => r.json());

const PLAGE_COLORS: Record<string, string> = {
  super_creuses: "text-green-400",
  creuses: "text-yellow-400",
  pleines: "text-red-400",
};

const PLAGE_LABELS: Record<string, string> = {
  super_creuses: "SUPER-CREUSE 🟢",
  creuses: "CREUSE 🟡",
  pleines: "PLEINE 🔴",
};

function formatMinutes(mins: number): string {
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return h > 0 ? `${h}h${String(m).padStart(2, "0")}` : `${m}min`;
}

export default function RealtimeCost() {
  const backend = process.env.NEXT_PUBLIC_BACKEND_URL;
  const { data, error } = useSWR(`${backend}/api/realtime`, fetcher, { refreshInterval: 10000 });

  if (error) return <Card title="Prix actuel"><p className="text-red-400 text-sm">Erreur de connexion</p></Card>;
  if (!data) return <Card title="Prix actuel"><p className="text-slate-500 text-sm animate-pulse">Chargement...</p></Card>;

  const plage = data.plage_active as string;
  const colorClass = PLAGE_COLORS[plage] || "text-slate-300";

  return (
    <Card title="Prix actuel">
      <div className="text-4xl font-bold tabular-nums">
        {(data.prix_kwh_actuel as number).toFixed(4)} <span className="text-xl font-normal text-slate-400">€/kWh</span>
      </div>
      <div className={`text-lg font-semibold mt-1 ${colorClass}`}>
        {PLAGE_LABELS[plage] || plage}
      </div>
      <div className="text-slate-400 text-sm mt-1">
        Changement dans : <span className="text-slate-200 font-medium">{formatMinutes(data.minutes_avant_changement)}</span>
      </div>
      <div className="text-slate-500 text-xs mt-1">
        EPEX : {(data.epex_eur_mwh as number).toFixed(1)} €/MWh · ORES : {data.plage_ores}
      </div>
    </Card>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-slate-900 rounded-2xl p-5 border border-slate-800 shadow-lg">
      <h2 className="text-xs font-semibold uppercase tracking-widest text-slate-500 mb-3">{title}</h2>
      {children}
    </div>
  );
}
