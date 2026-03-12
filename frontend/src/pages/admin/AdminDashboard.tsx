import { useQuery } from "@tanstack/react-query";
import { api } from "../../api/client";
import { Users, Activity, DollarSign, Key } from "lucide-react";

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

export default function AdminDashboard() {
  const { data: users } = useQuery({
    queryKey: ["admin-users"],
    queryFn: () => api.get("/admin/users?page=0&size=1").then((r) => r.data),
  });

  const { data: logs } = useQuery({
    queryKey: ["admin-logs"],
    queryFn: () => api.get("/admin/logs?page=0&size=10").then((r) => r.data),
  });

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h1 className="text-2xl font-bold">Admin Overview</h1>
        <p className="text-sm text-gray-500 mt-1">Platform statistics</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total Users" value={users?.total ?? "—"} icon={Users} color="bg-brand-600" />
        <StatCard label="Total Requests" value={logs?.total ?? "—"} icon={Activity} color="bg-purple-500" />
        <StatCard
          label="Revenue"
          value={
            logs?.items
              ? `$${logs.items.reduce((s: number, l: any) => s + l.cost, 0).toFixed(4)}`
              : "—"
          }
          icon={DollarSign}
          color="bg-green-500"
        />
        <StatCard label="Active Now" value="—" icon={Key} color="bg-orange-500" />
      </div>

      {/* Recent logs */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h2 className="text-sm font-semibold text-gray-700 mb-4">Recent Requests</h2>
        <div className="divide-y divide-gray-100">
          {logs?.items?.map((l: any) => (
            <div key={l.id} className="flex items-center justify-between py-2.5 text-sm">
              <div className="flex items-center gap-3">
                <span className="font-mono text-xs bg-gray-100 px-1.5 py-0.5 rounded">{l.method}</span>
                <span>{l.route}</span>
              </div>
              <div className="flex items-center gap-4 text-xs text-gray-500">
                <span className="text-gray-400">{l.user_email}</span>
                <span className="text-green-600">${l.cost.toFixed(6)}</span>
                <span>{new Date(l.created_at).toLocaleString()}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
