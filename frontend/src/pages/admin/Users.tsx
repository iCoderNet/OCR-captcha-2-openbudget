import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../api/client";
import { ChevronLeft, ChevronRight, PlusCircle } from "lucide-react";

interface GrantModalProps {
  userId: string;
  email: string;
  onClose: () => void;
}

function GrantModal({ userId, email, onClose }: GrantModalProps) {
  const qc = useQueryClient();
  const [amount, setAmount] = useState("1.0000");
  const [desc, setDesc] = useState("");
  const [done, setDone] = useState(false);

  const mutation = useMutation({
    mutationFn: () =>
      api.post(`/admin/users/${userId}/credits`, { amount: parseFloat(amount), description: desc }),
    onSuccess: () => {
      setDone(true);
      qc.invalidateQueries({ queryKey: ["admin-users-list"] });
      setTimeout(onClose, 1000);
    },
  });

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6 space-y-4">
        <h2 className="text-lg font-semibold">Grant Credits</h2>
        <p className="text-sm text-gray-500">{email}</p>
        <div>
          <label className="block text-sm font-medium mb-1">Amount ($)</label>
          <input
            type="number"
            step="0.0001"
            min="0.0001"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Description (optional)</label>
          <input
            type="text"
            value={desc}
            onChange={(e) => setDesc(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            placeholder="Reason..."
          />
        </div>
        {done && <p className="text-sm text-green-600">Credits granted!</p>}
        <div className="flex gap-2">
          <button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending || done}
            className="flex-1 rounded-lg bg-brand-600 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
          >
            Grant
          </button>
          <button
            onClick={onClose}
            className="flex-1 rounded-lg border border-gray-300 py-2 text-sm hover:bg-gray-50"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}

export default function Users() {
  const qc = useQueryClient();
  const [page, setPage] = useState(0);
  const [grantTarget, setGrantTarget] = useState<{ id: string; email: string } | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["admin-users-list", page],
    queryFn: () => api.get(`/admin/users?page=${page}&size=20`).then((r) => r.data),
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      api.patch(`/admin/users/${id}/toggle`, { is_active }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin-users-list"] }),
  });

  return (
    <div className="max-w-5xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Users</h1>
        <p className="text-sm text-gray-500 mt-1">{data?.total ?? 0} registered users</p>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
              <th className="text-left px-4 py-3">User</th>
              <th className="text-left px-4 py-3">Role</th>
              <th className="text-right px-4 py-3">Balance</th>
              <th className="text-left px-4 py-3">Status</th>
              <th className="text-right px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {isLoading && (
              <tr><td colSpan={5} className="text-center py-8 text-gray-400">Loading…</td></tr>
            )}
            {data?.items?.map((u: any) => (
              <tr key={u.id} className="hover:bg-gray-50">
                <td className="px-4 py-3">
                  <p className="font-medium">{u.full_name ?? u.email}</p>
                  <p className="text-xs text-gray-400">{u.email}</p>
                </td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    u.role === "admin" ? "bg-purple-100 text-purple-700" : "bg-gray-100 text-gray-600"
                  }`}>{u.role}</span>
                </td>
                <td className="px-4 py-3 text-right font-mono text-xs">${u.balance.toFixed(4)}</td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    u.is_active ? "bg-green-100 text-green-700" : "bg-red-100 text-red-600"
                  }`}>{u.is_active ? "Active" : "Suspended"}</span>
                </td>
                <td className="px-4 py-3 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <button
                      onClick={() => setGrantTarget({ id: u.id, email: u.email })}
                      className="text-xs flex items-center gap-1 text-brand-600 hover:text-brand-700"
                    >
                      <PlusCircle size={14} /> Credits
                    </button>
                    <button
                      onClick={() => toggleMutation.mutate({ id: u.id, is_active: !u.is_active })}
                      className="text-xs text-gray-500 hover:text-gray-700"
                    >
                      {u.is_active ? "Suspend" : "Activate"}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {data && data.pages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100">
            <span className="text-xs text-gray-500">Page {page + 1} of {data.pages}</span>
            <div className="flex gap-2">
              <button onClick={() => setPage((p) => Math.max(0, p - 1))} disabled={page === 0}
                className="p-1.5 rounded-lg border border-gray-200 disabled:opacity-40 hover:bg-gray-50">
                <ChevronLeft size={16} />
              </button>
              <button onClick={() => setPage((p) => p + 1)} disabled={page >= data.pages - 1}
                className="p-1.5 rounded-lg border border-gray-200 disabled:opacity-40 hover:bg-gray-50">
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        )}
      </div>

      {grantTarget && (
        <GrantModal
          userId={grantTarget.id}
          email={grantTarget.email}
          onClose={() => setGrantTarget(null)}
        />
      )}
    </div>
  );
}
