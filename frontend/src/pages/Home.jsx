import { Link } from "react-router-dom";

export default function Home() {
  return (
    <div style={{ padding: 32, fontFamily: "sans-serif" }}>
      <h1>FindOpp</h1>
      <p>Visitor home page (event search) goes here.</p>
      <Link to="/login">Sign in</Link> · <Link to="/register">Create an organizer account</Link>
    </div>
  );
}