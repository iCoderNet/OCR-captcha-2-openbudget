import { useEffect } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./hooks/useAuth";
import ProtectedRoute from "./components/layout/ProtectedRoute";
import Login from "./pages/auth/Login";
import Register from "./pages/auth/Register";
import Dashboard from "./pages/client/Dashboard";
import ApiKeys from "./pages/client/ApiKeys";
import Logs from "./pages/client/Logs";
import Balance from "./pages/client/Balance";
import AdminDashboard from "./pages/admin/AdminDashboard";
import Users from "./pages/admin/Users";
import Prices from "./pages/admin/Prices";
import AllLogs from "./pages/admin/AllLogs";

export default function App() {
  const { token, fetchMe } = useAuth();

  useEffect(() => {
    if (token) fetchMe();
  }, [token]);

  return (
    <BrowserRouter>
      <Routes>
        {/* Public */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Client */}
        <Route element={<ProtectedRoute role="client" />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/keys" element={<ApiKeys />} />
          <Route path="/logs" element={<Logs />} />
          <Route path="/balance" element={<Balance />} />
        </Route>

        {/* Admin */}
        <Route element={<ProtectedRoute role="admin" />}>
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/admin/users" element={<Users />} />
          <Route path="/admin/prices" element={<Prices />} />
          <Route path="/admin/logs" element={<AllLogs />} />
        </Route>

        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
