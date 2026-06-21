"use client";
import useSWR from "swr";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";

const fetcher = (url: string) => fetch(url).then((r) => r.json());

export default function AnalyticsPage() {
  const backend = process.env.NEXT_PUBLIC_BACKEND_URL;
  const { data, error } = useSWR(`${backend}/api/analytics`, fetcher, { refreshInterval: 300000 });

  if (error) return <p className="text-red-400 text-sm">Erreur de chargement</p>;
  if (!data) return <p className="text-slate-500 text-sm animate-pulse">Chargement...</p>;

  const donutData = [
    { name: "Voiture", value: data.kwh_voiture, color: "#3b82f6" },
    { name: "Maison", value: data.kwh_maison, color: "#8b5cf6" },
  ];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <StatCard label="Coût moyen réel" value={`${(data.cout_moyen_kwh_reel as number).toFixed(4)} €/kWh`} />
        <StatCard label="Coût par km BMW" value={`${(data.cout_par_km as number).toFixed(3)} €/km`} />
        <StatCard label="Sessions recharge" value={String(data.nb_sessions_recharge)} />
        <StatCard
          label="Économies vs fixe"
          value={`${(data.economies_vs_fixe as number).toFixed(2)} €`}
          valueColor={data.economies_vs_fixe > 0 ? "text-green-400" : "text-red-400"}
        />
      </div>

      <div className="bg-slate-900 rounded-2xl p-4 border border-slate-800">
        <h3 className="text-xs font-semibold uppercase tracking-widest text-slate-500 mb-4">
          Répartition consommation
        </h3>
        <ResponsiveContainer width="100%" height={200}>
          <PieChart>
            <Pie data={donutData} cx="50%" cy="50%" innerRadius={55} outerRadius={80} dataKey="value" stroke="none">
              {donutData.map((entry, i) => (
                <Cell key={i} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
              formatter={(v: number) => [`${v.toFixed(1)} kWh`]}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="flex justify-center gap-6 mt-2 text-sm">
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-blue-500 inline-block" />
            Voiture ({data.kwh_voiture.toFixed(1)} kWh · {data.cout_voiture.toFixed(2)} €)
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-violet-500 inline-block" />
            Maison ({data.kwh_maison.toFixed(1)} kWh · {data.cout_maison.toFixed(2)} €)
          </span>
        </div>
      </div>

      <div className="bg-slate-900 rounded-2xl p-4 border border-slate-800">
        <h3 className="text-xs font-semibold uppercase tracking-widest text-slate-500 mb-3">
          Comparaison tarif fixe (0,42 €/kWh)
        </h3>
        <div className="space-y-2 text-sm">
          <Row label="Tarif fixe estimé" value={`${(data.kwh_total * 0.42).toFixed(2)} €`} />
          <Row
            label="Coût réel Flextime"
            value={`${(data.cout_voiture + data.cout_maison).toFixed(2)} €`}
          />
          <Row
            label="Économies"
            value={`${data.economies_vs_fixe.toFixed(2)} €`}
            valueColor={data.economies_vs_fixe > 0 ? "text-green-400" : "text-red-400"}
          />
        </div>
      </div>
    </div>
  );
}

function StatCard({
  label, value, valueColor = "text-slate-100",
}: {
  label: string; value: string; valueColor?: string;
}) {
  return (
    <div className="bg-slate-900 rounded-xl p-4 border border-slate-800">
      <div className="text-xs text-slate-500 mb-1">{label}</div>
      <div className={`text-lg font-bold ${valueColor}`}>{value}</div>
    </div>
  );
}

function Row({ label, value, valueColor = "text-slate-200" }: { label: string; value: string; valueColor?: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-slate-400">{label}</span>
      <span className={`font-medium ${valueColor}`}>{value}</span>
    </div>
  );
}
