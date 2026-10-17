const BASE_URL = "http://localhost:8000";

export const getToken = () => localStorage.getItem("token");
export const setToken = (t) => localStorage.setItem("token", t);
export const clearToken = () => localStorage.removeItem("token");

export async function apiFetch(path, { method = "GET", body } = {}) {
  const headers = {};
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let payload = body;
  if (body && !(body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  let res;
  try {
    res = await fetch(BASE_URL + path, { method, headers, body: payload });
  } catch {
    throw new Error("Can't reach the server. Is the backend running?");
  }

  if (!res.ok) {
    // Expired or invalid token on a protected call: log out.
    // Login and register also return 401/409, so skip those paths.
    const isAuthCall = path === "/login" || path === "/register";
    if (res.status === 401 && !isAuthCall && token) {
      clearToken();
      window.location.href = "/login";
    }

    let message = "Something went wrong";
    try {
      const data = await res.json();
      if (typeof data.detail === "string") message = data.detail;
      else if (Array.isArray(data.detail)) message = "Please check your input";
    } catch {}

    const error = new Error(message);
    error.status = res.status;
    throw error;
  }

  if (res.status === 204) return null;
  return res.json();
}