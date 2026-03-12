import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Key,
  ScrollText,
  Wallet,
  Users,
  DollarSign,
  LogOut,
  Activity,
} from "lucide-react";
import { useAuth } from "../../hooks/useAuth";
import clsx from "clsx";

const clientLinks = [
  { to: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/keys", icon: Key, label: "API Keys" },
  { to: "/logs", icon: ScrollText, label: "Usage Logs" },
  { to: "/balance", icon: Wallet, label: "Balance" },
];

const adminLinks = [
  { to: "/admin", icon: LayoutDashboard, label: "Overview" },
  { to: "/admin/users", icon: Users, label: "Users" },
  { to: "/admin/prices", icon: DollarSign, label: "Pricing" },
  { to: "/admin/logs", icon: Activity, label: "All Logs" },
];

export default function Sidebar() {
  const { user, logout } = useAuth();
  const links = user?.role === "admin" ? adminLinks : clientLinks;

  return (
    <aside className="flex h-screen w-56 flex-col bg-gray-900 text-white">
      {/* Logo */}
      <div className="flex h-14 items-center gap-2 px-4 border-b border-gray-700">
        <div className="h-7 w-7 rounded-md bg-brand-600 flex items-center justify-center text-xs font-bold">
          OB
        </div>
        <span className="font-semibold text-sm">OpenBudget API</span>
      </div>

      {/* User info */}
      <div className="px-4 py-3 border-b border-gray-700">
        <p className="text-xs text-gray-400 truncate">{user?.email}</p>
        <p className="text-sm font-medium">
          Balance:{" "}
          <span className="text-green-400">${user?.balance.toFixed(4)}</span>
        </p>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto p-2 space-y-0.5">
        {links.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/admin"}
            className={({ isActive }) =>
              clsx(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
                isActive
                  ? "bg-brand-600 text-white"
                  : "text-gray-300 hover:bg-gray-800 hover:text-white"
              )
            }
          >
            <Icon size={16} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Logout */}
      <div className="p-2 border-t border-gray-700">
        <button
          onClick={logout}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-gray-300 hover:bg-gray-800 hover:text-white transition-colors"
        >
          <LogOut size={16} />
          Logout
        </button>
      </div>
    </aside>
  );
}
