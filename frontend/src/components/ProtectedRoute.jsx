import { Navigate } from "react-router-dom";
import { getToken } from "../api";

// Pages that need a login (the chat).
export function ProtectedRoute({ children }) {
  if (!getToken()) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

// Pages for logged-out users only (login, register).
export function PublicRoute({ children }) {
  if (getToken()) {
    return <Navigate to="/" replace />;
  }
  return children;
}

export default ProtectedRoute;