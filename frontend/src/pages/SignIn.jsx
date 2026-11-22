import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import AuthHero from "./AuthHero";
import { login } from "../api/auth";
import { useAuth, ROLE_HOME } from "../context/AuthContext";
import "./SignIn.css";

export default function SignIn() {
  const { signIn } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    if (!email || !password) return setError("Enter your email address and password.");

    setLoading(true);
    try {
      const data = await login(email, password);
      const user = signIn(data, email, remember);
      // Role is recognized automatically: go straight to the user's space
      navigate(location.state?.from || ROLE_HOME[user.role] || "/", { replace: true });
    } catch (err) {
      // e.g. 403 "Your account is awaiting verification"
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="si">
      <AuthHero />
      <main className="si-panel">
        <Link className="si-back" to="/">← Back to FindOpp</Link>

        <form className="si-form" onSubmit={handleSubmit} noValidate>
          <span className="si-eyebrow">Sign in</span>
          <h1 className="si-title">Welcome <em>back.</em></h1>
          <p className="si-sub">One sign-in for organizers and administrators.</p>

          <label className="si-label" htmlFor="email">Email address</label>
          <input id="email" className="si-input" type="email" autoComplete="email"
            value={email} onChange={(e) => setEmail(e.target.value)} required />

          <label className="si-label" htmlFor="password">Password</label>
          <input id="password" className="si-input" type="password" autoComplete="current-password"
            value={password} onChange={(e) => setPassword(e.target.value)} required />

          <div className="si-row">
            <label className="si-check">
              <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} />
              <span>Keep me signed in</span>
            </label>
            <Link className="si-link" to="/forgot-password">Forgot your password?</Link>
          </div>

          {error ? (
            <div className="si-note si-note--error" role="alert">{error}</div>
          ) : (
            <div className="si-note">
              <strong>Your role is recognized automatically after sign-in.</strong>
              <span>You’ll go straight to your space.</span>
            </div>
          )}

          <button className="si-btn" type="submit" disabled={loading}>
            {loading ? "Signing in…" : "Sign in"}
          </button>

          <Link className="si-create" to="/register">Create an organizer account</Link>
          <p className="si-foot">Visitors can browse FindOpp freely, without an account.</p>
        </form>
      </main>
    </div>
  );
}
