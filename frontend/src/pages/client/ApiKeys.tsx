import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../api/client";
import { Plus, Copy, Trash2, ToggleLeft, ToggleRight, CheckCircle } from "lucide-react";

export default function ApiKeys() {
  const qc = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [newKeyName, setNewKeyName] = useState("My Key");
  const [createdKey, setCreatedKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const { data: keys = [], isLoading } = useQuery({
    queryKey: ["keys"],
    queryFn: () => api.get("/client/keys").then((r) => r.data),
  });

  const createMutation = useMutation({
    mutationFn: (name: string) => api.post("/client/keys", { name }).then((r) => r.data),
    onSuccess: (data) => {
      setCreatedKey(data.raw_key);
      setShowCreate(false);
      qc.invalidateQueries({ queryKey: ["keys"] });
    },
  });

  const toggleMutation = useMutation({
    mutationFn: (id: string) => api.patch(`/client/keys/${id}/toggle`).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["keys"] }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/client/keys/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["keys"] }),
  });

  function copyKey(key: string) {
    navigator.clipboard.writeText(key);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="max-w-3xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">API Keys</h1>
          <p className="text-sm text-gray-500 mt-1">
            Use <code className="bg-gray-100 px-1 rounded">X-API-Key</code> header to authenticate requests.
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 transition-colors"
        >
          <Plus size={16} /> New Key
        </button>
      </div>

      {/* Newly created key banner */}
      {createdKey && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle size={16} className="text-green-600" />
            <p className="text-sm font-medium text-green-800">Key created — copy it now, it won't be shown again.</p>
          </div>
          <div className="flex items-center gap-2">
            <code className="flex-1 text-sm bg-white border border-green-200 rounded-lg px-3 py-2 font-mono truncate">
              {createdKey}
            </code>
            <button
              onClick={() => copyKey(createdKey)}
              className="flex items-center gap-1 rounded-lg bg-green-600 px-3 py-2 text-xs text-white hover:bg-green-700"
            >
              <Copy size={14} />
              {copied ? "Copied!" : "Copy"}
            </button>
          </div>
        </div>
      )}

      {/* Create form */}
      {showCreate && (
        <div className="bg-white border border-gray-200 rounded-xl p-4 space-y-3">
          <h2 className="text-sm font-semibold">New API Key</h2>
          <input
            type="text"
            value={newKeyName}
            onChange={(e) => setNewKeyName(e.target.value)}
            placeholder="Key name"
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
          <div className="flex gap-2">
            <button
              onClick={() => createMutation.mutate(newKeyName)}
              disabled={createMutation.isPending}
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
            >
              Create
            </button>
            <button
              onClick={() => setShowCreate(false)}
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm hover:bg-gray-50"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Keys list */}
      <div className="bg-white rounded-xl border border-gray-200 divide-y divide-gray-100">
        {isLoading && (
          <div className="p-6 text-center text-sm text-gray-400">Loading…</div>
        )}
        {!isLoading && keys.length === 0 && (
          <div className="p-6 text-center text-sm text-gray-400">
            No API keys yet. Create one above.
          </div>
        )}
        {keys.map((key: any) => (
          <div key={key.id} className="flex items-center justify-between px-4 py-3">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <p className="text-sm font-medium truncate">{key.name}</p>
                <span
                  className={`text-xs px-2 py-0.5 rounded-full ${
                    key.is_active
                      ? "bg-green-100 text-green-700"
                      : "bg-gray-100 text-gray-500"
                  }`}
                >
                  {key.is_active ? "Active" : "Disabled"}
                </span>
              </div>
              <p className="text-xs text-gray-400 mt-0.5">
                {key.total_requests.toLocaleString()} requests · $
                {key.total_spent.toFixed(4)} spent ·{" "}
                {key.last_used_at
                  ? `last used ${new Date(key.last_used_at).toLocaleDateString()}`
                  : "never used"}
              </p>
            </div>
            <div className="flex items-center gap-1 ml-4">
              <button
                onClick={() => toggleMutation.mutate(key.id)}
                className="p-2 rounded-lg hover:bg-gray-100 transition-colors text-gray-500"
                title={key.is_active ? "Disable" : "Enable"}
              >
                {key.is_active ? (
                  <ToggleRight size={18} className="text-green-500" />
                ) : (
                  <ToggleLeft size={18} />
                )}
              </button>
              <button
                onClick={() => {
                  if (confirm("Delete this key?")) deleteMutation.mutate(key.id);
                }}
                className="p-2 rounded-lg hover:bg-red-50 text-gray-400 hover:text-red-500 transition-colors"
              >
                <Trash2 size={16} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
