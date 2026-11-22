import { useAuth } from "../../context/AuthContext";

export default function OrganizerDashboard() {
  const { user, signOut } = useAuth();
  return (
    <div style={{ padding: 32, fontFamily: "sans-serif" }}>
      <h1>Organizer space</h1>
      <p>Signed in as {user.email}</p>
      <button onClick={signOut}>Sign out</button>
    </div>
  );
}