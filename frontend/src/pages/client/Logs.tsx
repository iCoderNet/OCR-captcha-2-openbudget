import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../api/client";
import { ChevronLeft, ChevronRight } from "lucide-react";

function StatusBadge({ code }: { code: number | null }) {
  if (!code) return <span className="text-gray-400">—</span>;
  const cls =
    code < 300
      ? "bg-green-100 text-green-700"
      : code < 500
      ? "bg-yellow-100 text-yellow-700"
      : "bg-red-100 text-red-700";
  return <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${cls}`}>{code}</span>;
}

export default function Logs() {
  const [page, setPage] = useState(0);

  const { data, isLoading } = useQuery({
    queryKey: ["logs", page],
    queryFn: () => api.get(`/client/logs?page=${page}&size=20`).then((r) => r.data),
  });

  return (
    <div className="max-w-5xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Usage Logs</h1>
        <p className="text-sm text-gray-500 mt-1">
          {data?.total ?? 0} total requests
        </p>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
              <th className="text-left px-4 py-3">Route</th>
              <th className="text-left px-4 py-3">Status</th>
              <th className="text-right px-4 py-3">Cost</th>
              <th className="text-right px-4 py-3">Time</th>
              <th className="text-right px-4 py-3">Date</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {isLoading && (
              <tr>
                <td colSpan={5} className="text-center py-8 text-gray-400">Loading…</td>
              </tr>
            )}
            {!isLoading && data?.items?.length === 0 && (
              <tr>
                <td colSpan={5} className="text-center py-8 text-gray-400">No logs yet.</td>
              </tr>
            )}
            {data?.items?.map((l: any) => (
              <tr key={l.id} className="hover:bg-gray-50">
                <td className="px-4 py-2.5">
                  <span className="font-mono text-xs bg-gray-100 px-1.5 py-0.5 rounded mr-2">
                    {l.method}
                  </span>
                  <span className="text-gray-700">{l.route}</span>
                </td>
                <td className="px-4 py-2.5">
                  <StatusBadge code={l.status_code} />
                </td>
                <td className="px-4 py-2.5 text-right font-mono text-xs">
                  ${l.cost.toFixed(6)}
                </td>
                <td className="px-4 py-2.5 text-right text-gray-500">
                  {l.response_time_ms ?? "—"}ms
                </td>
                <td className="px-4 py-2.5 text-right text-gray-400 text-xs">
                  {new Date(l.created_at).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Pagination */}
        {data && data.pages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100">
            <span className="text-xs text-gray-500">
              Page {page + 1} of {data.pages}
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
                className="p-1.5 rounded-lg border border-gray-200 disabled:opacity-40 hover:bg-gray-50"
              >
                <ChevronLeft size={16} />
              </button>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={page >= data.pages - 1}
                className="p-1.5 rounded-lg border border-gray-200 disabled:opacity-40 hover:bg-gray-50"
              >
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
