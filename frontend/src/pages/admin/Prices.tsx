import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../api/client";
import { Plus, Pencil, Trash2, Check, X } from "lucide-react";

interface Price {
  id: number;
  route_pattern: string;
  method: string;
  cost: number;
  description: string | null;
  is_active: boolean;
}

interface EditRowProps {
  price: Price;
  onCancel: () => void;
  onSave: (data: Partial<Price>) => void;
}

function EditRow({ price, onCancel, onSave }: EditRowProps) {
  const [form, setForm] = useState({
    route_pattern: price.route_pattern,
    method: price.method,
    cost: price.cost.toFixed(6),
    description: price.description ?? "",
    is_active: price.is_active,
  });

  return (
    <tr className="bg-blue-50">
      <td className="px-4 py-2">
        <input
          value={form.method}
          onChange={(e) => setForm({ ...form, method: e.target.value })}
          className="w-20 rounded border border-gray-300 px-2 py-1 text-xs font-mono"
        />
      </td>
      <td className="px-4 py-2">
        <input
          value={form.route_pattern}
          onChange={(e) => setForm({ ...form, route_pattern: e.target.value })}
          className="w-full rounded border border-gray-300 px-2 py-1 text-xs font-mono"
        />
      </td>
      <td className="px-4 py-2">
        <input
          type="number"
          step="0.000001"
          value={form.cost}
          onChange={(e) => setForm({ ...form, cost: e.target.value })}
          className="w-28 rounded border border-gray-300 px-2 py-1 text-xs"
        />
      </td>
      <td className="px-4 py-2">
        <input
          value={form.description}
          onChange={(e) => setForm({ ...form, description: e.target.value })}
          className="w-full rounded border border-gray-300 px-2 py-1 text-xs"
        />
      </td>
      <td className="px-4 py-2 text-right">
        <div className="flex items-center justify-end gap-1">
          <button onClick={() => onSave({ ...form, cost: parseFloat(form.cost) })}
            className="p-1.5 rounded bg-green-100 text-green-700 hover:bg-green-200">
            <Check size={14} />
          </button>
          <button onClick={onCancel}
            className="p-1.5 rounded bg-gray-100 text-gray-600 hover:bg-gray-200">
            <X size={14} />
          </button>
        </div>
      </td>
    </tr>
  );
}

export default function Prices() {
  const qc = useQueryClient();
  const [editing, setEditing] = useState<number | null>(null);
  const [showAdd, setShowAdd] = useState(false);
  const [newForm, setNewForm] = useState({ method: "GET", route_pattern: "", cost: "0.001000", description: "" });

  const { data: prices = [], isLoading } = useQuery<Price[]>({
    queryKey: ["admin-prices"],
    queryFn: () => api.get("/admin/prices").then((r) => r.data),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) =>
      api.put(`/admin/prices/${id}`, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin-prices"] });
      setEditing(null);
    },
  });

  const createMutation = useMutation({
    mutationFn: (data: any) => api.post("/admin/prices", data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin-prices"] });
      setShowAdd(false);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/admin/prices/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin-prices"] }),
  });

  return (
    <div className="max-w-5xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Route Pricing</h1>
          <p className="text-sm text-gray-500 mt-1">Cost per request for each API route</p>
        </div>
        <button
          onClick={() => setShowAdd(true)}
          className="flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
        >
          <Plus size={16} /> Add Route
        </button>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
              <th className="text-left px-4 py-3 w-20">Method</th>
              <th className="text-left px-4 py-3">Route Pattern</th>
              <th className="text-left px-4 py-3 w-32">Cost (USD)</th>
              <th className="text-left px-4 py-3">Description</th>
              <th className="text-right px-4 py-3 w-24">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {isLoading && <tr><td colSpan={5} className="text-center py-8 text-gray-400">Loading…</td></tr>}

            {showAdd && (
              <tr className="bg-green-50">
                <td className="px-4 py-2">
                  <select value={newForm.method} onChange={(e) => setNewForm({ ...newForm, method: e.target.value })}
                    className="rounded border border-gray-300 px-2 py-1 text-xs">
                    {["GET", "POST", "PUT", "DELETE", "*"].map((m) => <option key={m}>{m}</option>)}
                  </select>
                </td>
                <td className="px-4 py-2">
                  <input value={newForm.route_pattern} onChange={(e) => setNewForm({ ...newForm, route_pattern: e.target.value })}
                    placeholder="/route/{param}" className="w-full rounded border border-gray-300 px-2 py-1 text-xs font-mono" />
                </td>
                <td className="px-4 py-2">
                  <input type="number" step="0.000001" value={newForm.cost} onChange={(e) => setNewForm({ ...newForm, cost: e.target.value })}
                    className="w-full rounded border border-gray-300 px-2 py-1 text-xs" />
                </td>
                <td className="px-4 py-2">
                  <input value={newForm.description} onChange={(e) => setNewForm({ ...newForm, description: e.target.value })}
                    className="w-full rounded border border-gray-300 px-2 py-1 text-xs" />
                </td>
                <td className="px-4 py-2 text-right">
                  <div className="flex items-center justify-end gap-1">
                    <button onClick={() => createMutation.mutate({ ...newForm, cost: parseFloat(newForm.cost), is_active: true })}
                      className="p-1.5 rounded bg-green-100 text-green-700 hover:bg-green-200"><Check size={14} /></button>
                    <button onClick={() => setShowAdd(false)} className="p-1.5 rounded bg-gray-100 text-gray-600 hover:bg-gray-200"><X size={14} /></button>
                  </div>
                </td>
              </tr>
            )}

            {prices.map((p) =>
              editing === p.id ? (
                <EditRow
                  key={p.id}
                  price={p}
                  onCancel={() => setEditing(null)}
                  onSave={(data) => updateMutation.mutate({ id: p.id, data: { ...p, ...data } })}
                />
              ) : (
                <tr key={p.id} className={`hover:bg-gray-50 ${!p.is_active ? "opacity-50" : ""}`}>
                  <td className="px-4 py-2.5">
                    <span className="text-xs font-mono bg-gray-100 px-2 py-0.5 rounded">{p.method}</span>
                  </td>
                  <td className="px-4 py-2.5 font-mono text-xs text-gray-700">{p.route_pattern}</td>
                  <td className="px-4 py-2.5 font-medium text-green-700">${p.cost.toFixed(6)}</td>
                  <td className="px-4 py-2.5 text-xs text-gray-500">{p.description ?? "—"}</td>
                  <td className="px-4 py-2.5 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <button onClick={() => setEditing(p.id)} className="p-1.5 rounded hover:bg-gray-100 text-gray-500">
                        <Pencil size={14} />
                      </button>
                      <button onClick={() => { if (confirm("Delete?")) deleteMutation.mutate(p.id); }}
                        className="p-1.5 rounded hover:bg-red-50 text-gray-400 hover:text-red-500">
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              )
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
