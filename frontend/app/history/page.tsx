"use client";
import { useState } from "react";
import useSWR from "swr";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from "recharts";

const fetcher = (url: string) => fetch(url).then((r) => r.json());

const PLAGE_COLORS: Record<string, string> = {
  super_creuses: "#22c55e",
  creuses: "#eab308",
  pleines: "#ef4444",
};

type Filter = "today" | "7d" | "30d";

function getFromTs(filter: Filter): string {
  const now = new Date();
  if (filter === "today") {
    now.setHours(0, 0, 0, 0);
  } else if (filter === "7d") {
    now.setDate(now.getDate() - 7);
  } else {
    now.setDate(now.getDate() - 30);
  }
  return now.toISOString();
}

export default function HistoryPage() {
  const [filter, setFilter] = useState<Filter>("today");
  const backend = process.env.NEXT_PUBLIC_BACKEND_URL;
  const from = getFromTs(filter);
  const gran = filter === "30d" ? "1h" : "15min";

  const { data, error } = useSWR(
    `${backend}/api/history?granularity=${gran}&from_ts=${from}`,
    fetcher,
    { refreshInterval: 60000 },
  );

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        {(["today", "7d", "30d"] as Filter[]).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
              filter === f
                ? "bg-blue-600 text-white"
                : "bg-slate-800 text-slate-400 hover:bg-slate-700"
            }`}
          >
            {f === "today" ? "Aujourd'hui" : f === "7d" ? "7 jours" : "30 jours"}
          </button>
        ))}
      </div>

      <div className="bg-slate-900 rounded-2xl p-4 border border-slate-800">
        <div className="flex gap-4 text-xs text-slate-400 mb-4">
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm bg-green-500 inline-block" />Super-creuse</span>
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm bg-yellow-500 inline-block" />Creuse</span>
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm bg-red-500 inline-block" />Pleine</span>
        </div>

        {error && <p className="text-red-400 text-sm">Erreur de chargement</p>}
        {!data && !error && <p className="text-slate-500 text-sm animate-pulse">Chargement...</p>}
        {data && (
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={data} margin={{ top: 0, right: 0, bottom: 0, left: -20 }}>
              <XAxis
                dataKey="timestamp"
                tick={{ fill: "#64748b", fontSize: 10 }}
                tickFormatter={(v) => {
                  const d = new Date(v);
                  return filter === "today"
                    ? `${d.getHours()}h`
                    : `${d.getDate()}/${d.getMonth() + 1}`;
                }}
                interval="preserveStartEnd"
              />
              <YAxis tick={{ fill: "#64748b", fontSize: 10 }} unit=" W" />
              <Tooltip
                contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
                labelStyle={{ color: "#94a3b8", fontSize: 11 }}
                formatter={(v: number, name: string) => [
                  name === "watts" ? `${v} W` : `${v} kWh`,
                  name === "watts" ? "Puissance" : "Énergie",
                ]}
              />
              <Bar dataKey="watts" radius={[2, 2, 0, 0]}>
                {data.map((entry: { plage: string; est_recharge: boolean }, i: number) => (
                  <Cell
                    key={i}
                    fill={PLAGE_COLORS[entry.plage] || "#64748b"}
                    fillOpacity={entry.est_recharge ? 0.5 : 1}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {data && (
        <div className="bg-slate-900 rounded-2xl p-4 border border-slate-800 text-sm">
          <div className="flex justify-between text-slate-400">
            <span>Total période</span>
            <span className="text-slate-200 font-medium">
              {(data as Array<{ kwh: number }>).reduce((s, r) => s + r.kwh, 0).toFixed(2)} kWh
            </span>
          </div>
          <div className="flex justify-between text-slate-400 mt-1">
            <span>Coût estimé</span>
            <span className="text-slate-200 font-medium">
              {(data as Array<{ cout: number }>).reduce((s, r) => s + r.cout, 0).toFixed(2)} €
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
