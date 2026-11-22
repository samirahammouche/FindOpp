import { useAuth } from "../../context/AuthContext";

export default function AdminDashboard() {
  const { user, signOut } = useAuth();
  return (
    <div style={{ padding: 32, fontFamily: "sans-serif" }}>
      <h1>Admin space</h1>
      <p>Signed in as {user.email}</p>
      <button onClick={signOut}>Sign out</button>
    </div>
  );
}