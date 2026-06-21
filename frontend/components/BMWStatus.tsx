"use client";
import useSWR from "swr";

const fetcher = (url: string) => fetch(url).then((r) => r.json());

export default function BMWStatus() {
  const backend = process.env.NEXT_PUBLIC_BACKEND_URL;
  const { data: bmw, error: bmwErr } = useSWR(`${backend}/api/bmw`, fetcher, { refreshInterval: 60000 });
  const { data: rt } = useSWR(`${backend}/api/realtime`, fetcher, { refreshInterval: 10000 });

  if (bmwErr) return <Card><p className="text-red-400 text-sm">BMW non disponible</p></Card>;
  if (!bmw) return <Card><p className="text-slate-500 text-sm animate-pulse">Chargement...</p></Card>;

  const isCharging = bmw.charging_status === "CHARGING";
  const batteryColor =
    bmw.battery_percent > 60 ? "text-green-400" : bmw.battery_percent > 30 ? "text-yellow-400" : "text-red-400";

  return (
    <Card>
      <div className="flex items-center justify-between mb-3">
        <span className={`text-3xl font-bold ${batteryColor}`}>
          {bmw.battery_percent ?? "—"}%
          <span className="text-lg ml-1">🔋</span>
        </span>
        <span className="text-slate-300 text-lg font-medium">{bmw.range_km ?? "—"} km</span>
      </div>

      {isCharging && rt?.session_recharge && (
        <div className="bg-blue-950/50 rounded-xl p-3 border border-blue-800/50">
          <div className="text-blue-300 text-sm font-semibold">⚡ Recharge en cours</div>
          <div className="flex justify-between mt-1 text-sm">
            <span className="text-slate-400">{(rt.kwh_session as number).toFixed(2)} kWh</span>
            <span className="text-slate-200 font-medium">{(rt.cout_session as number).toFixed(2)} €</span>
          </div>
        </div>
      )}

      {!isCharging && (
        <div className="text-slate-500 text-sm">Non branché</div>
      )}
    </Card>
  );
}

function Card({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-slate-900 rounded-2xl p-5 border border-slate-800 shadow-lg">
      <h2 className="text-xs font-semibold uppercase tracking-widest text-slate-500 mb-3">BMW</h2>
      {children}
    </div>
  );
}
