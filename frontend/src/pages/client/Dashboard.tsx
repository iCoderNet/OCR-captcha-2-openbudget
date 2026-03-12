import { useQuery } from "@tanstack/react-query";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { api } from "../../api/client";
import { useAuth } from "../../hooks/useAuth";
import { Activity, Key, DollarSign, TrendingDown } from "lucide-react";

function StatCard({ label, value, icon: Icon, color }: any) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 flex items-center gap-4">
      <div className={`h-10 w-10 rounded-lg flex items-center justify-center ${color}`}>
        <Icon size={20} className="text-white" />
      </div>
      <div>
        <p className="text-sm text-gray-500">{label}</p>
        <p className="text-xl font-semibold">{value}</p>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { user, fetchMe } = useAuth();

  const { data: logsData } = useQuery({
    queryKey: ["logs", 0],
    queryFn: () => api.get("/client/logs?page=0&size=5").then((r) => r.data),
  });

  const { data: txData } = useQuery({
    queryKey: ["txns", 0],
    queryFn: () => api.get("/client/balance/transactions?page=0&size=30").then((r) => r.data),
  });

  const { data: keysData } = useQuery({
    queryKey: ["keys"],
    queryFn: () => api.get("/client/keys").then((r) => r.data),
  });

  // Build daily spend chart from transactions
  const dailyChart = (() => {
    if (!txData?.items) return [];
    const map: Record<string, number> = {};
    for (const t of txData.items) {
      if (t.amount >= 0) continue;
      const day = t.created_at.slice(0, 10);
      map[day] = (map[day] ?? 0) + Math.abs(t.amount);
    }
    return Object.entries(map)
      .sort()
      .slice(-14)
      .map(([date, cost]) => ({ date: date.slice(5), cost: +cost.toFixed(4) }));
  })();

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-gray-500 text-sm mt-1">Welcome back, {user?.full_name ?? user?.email}</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Balance"
          value={`$${user?.balance.toFixed(4) ?? "0.0000"}`}
          icon={DollarSign}
          color="bg-green-500"
        />
        <StatCard
          label="Active Keys"
          value={keysData?.filter((k: any) => k.is_active).length ?? 0}
          icon={Key}
          color="bg-brand-600"
        />
        <StatCard
          label="Total Requests"
          value={keysData?.reduce((s: number, k: any) => s + k.total_requests, 0) ?? 0}
          icon={Activity}
          color="bg-purple-500"
        />
        <StatCard
          label="Total Spent"
          value={`$${(keysData?.reduce((s: number, k: any) => s + k.total_spent, 0) ?? 0).toFixed(4)}`}
          icon={TrendingDown}
          color="bg-orange-500"
        />
      </div>

      {/* Chart */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h2 className="text-sm font-semibold text-gray-700 mb-4">Daily Spend (last 14 days)</h2>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={dailyChart} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="date" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip formatter={(v: any) => `$${v}`} />
            <Bar dataKey="cost" fill="#3b82f6" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Recent logs */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h2 className="text-sm font-semibold text-gray-700 mb-4">Recent Requests</h2>
        {logsData?.items?.length === 0 && (
          <p className="text-sm text-gray-400">No requests yet.</p>
        )}
        <div className="divide-y divide-gray-100">
          {logsData?.items?.map((l: any) => (
            <div key={l.id} className="flex items-center justify-between py-2.5">
              <div className="flex items-center gap-3">
                <span className="text-xs font-mono bg-gray-100 px-2 py-0.5 rounded">
                  {l.method}
                </span>
                <span className="text-sm text-gray-700">{l.route}</span>
              </div>
              <div className="flex items-center gap-4 text-xs text-gray-500">
                <span
                  className={
                    l.status_code < 300
                      ? "text-green-600"
                      : l.status_code < 500
                      ? "text-yellow-600"
                      : "text-red-600"
                  }
                >
                  {l.status_code}
                </span>
                <span>${l.cost.toFixed(6)}</span>
                <span>{l.response_time_ms}ms</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
