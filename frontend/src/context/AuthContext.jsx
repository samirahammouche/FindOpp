import { createContext, useContext, useState } from "react";
import { session } from "../api/client";

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export const ROLE_HOME = { admin: "/admin", organizer: "/organizer" };

function decodeJwt(token) {
  try {
    const part = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    return JSON.parse(atob(part));
  } catch {
    return {};
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => (session.token() ? session.user() : null));

  // data = login response from the auth service ({ access, refresh })
  function signIn(data, email, remember) {
    const claims = decodeJwt(data.access);
    const role = String(data.role || data.user?.role || claims.role || "").toLowerCase();
    const u = { email: claims.email || email, role };
    session.save(data.access, u, remember);
    setUser(u);
    return u;
  }

  function signOut() {
    session.clear();
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}