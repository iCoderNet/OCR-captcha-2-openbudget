import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../api/client";
import { useAuth } from "../../hooks/useAuth";
import { ChevronLeft, ChevronRight, ArrowUpRight, ArrowDownLeft } from "lucide-react";

export default function Balance() {
  const { user } = useAuth();
  const [page, setPage] = useState(0);

  const { data } = useQuery({
    queryKey: ["txns", page],
    queryFn: () =>
      api.get(`/client/balance/transactions?page=${page}&size=20`).then((r) => r.data),
  });

  return (
    <div className="max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold">Balance</h1>

      {/* Balance card */}
      <div className="bg-gradient-to-br from-brand-600 to-brand-700 rounded-2xl p-6 text-white">
        <p className="text-sm text-blue-200">Available balance</p>
        <p className="text-4xl font-bold mt-1">${user?.balance.toFixed(4)}</p>
        <p className="text-sm text-blue-200 mt-3">
          To top up, contact the administrator or request a top-up in the portal.
        </p>
      </div>

      {/* Transactions */}
      <div>
        <h2 className="text-sm font-semibold text-gray-700 mb-3">
          Transactions ({data?.total ?? 0})
        </h2>
        <div className="bg-white rounded-xl border border-gray-200 divide-y divide-gray-100">
          {data?.items?.length === 0 && (
            <p className="text-center py-8 text-sm text-gray-400">No transactions yet.</p>
          )}
          {data?.items?.map((t: any) => (
            <div key={t.id} className="flex items-center justify-between px-4 py-3">
              <div className="flex items-center gap-3">
                <div
                  className={`h-8 w-8 rounded-full flex items-center justify-center ${
                    t.amount >= 0 ? "bg-green-100" : "bg-red-50"
                  }`}
                >
                  {t.amount >= 0 ? (
                    <ArrowUpRight size={14} className="text-green-600" />
                  ) : (
                    <ArrowDownLeft size={14} className="text-red-500" />
                  )}
                </div>
                <div>
                  <p className="text-sm text-gray-700">{t.description ?? t.type}</p>
                  <p className="text-xs text-gray-400">
                    {new Date(t.created_at).toLocaleString()}
                  </p>
                </div>
              </div>
              <span
                className={`text-sm font-medium ${
                  t.amount >= 0 ? "text-green-600" : "text-red-500"
                }`}
              >
                {t.amount >= 0 ? "+" : ""}${t.amount.toFixed(6)}
              </span>
            </div>
          ))}
        </div>

        {data && data.pages > 1 && (
          <div className="flex items-center justify-between mt-3">
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
