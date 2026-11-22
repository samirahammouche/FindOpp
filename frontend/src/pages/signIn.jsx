import { useState } from "react";
import AuthLayout from "../AuthLayout.jsx";
import { readApiResponse } from "../api.js";
import "../auth.css";

function getRole(accessToken) {
  try {
    const encodedPayload = accessToken.split(".")[1];
    if (!encodedPayload) return "";
    const base64 = encodedPayload.replace(/-/g, "+").replace(/_/g, "/");
    const payload = JSON.parse(atob(base64.padEnd(Math.ceil(base64.length / 4) * 4, "=")));
    return payload.role || "";
  } catch {
    return "";
  }
}

export default function SignIn() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setNotice("");
    setLoading(true);

    try {
      const response = await fetch("/api/auth/login/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await readApiResponse(
        response,
        "Email or password is incorrect, or your organizer account is still being reviewed.",
      );

      if (!data.access || !data.refresh) {
        throw new Error("The server did not return the required sign-in tokens.");
      }

      const storage = remember ? localStorage : sessionStorage;
      localStorage.removeItem("findopp_access");
      localStorage.removeItem("findopp_refresh");
      sessionStorage.removeItem("findopp_access");
      sessionStorage.removeItem("findopp_refresh");
      storage.setItem("findopp_access", data.access);
      storage.setItem("findopp_refresh", data.refresh);

      const role = getRole(data.access);
      setNotice(
        role
          ? `Signed in successfully as ${role.toLowerCase()}.`
          : "Signed in successfully.",
      );
    } catch (submitError) {
      setError(
        submitError instanceof Error
          ? submitError.message
          : "Unable to sign in. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout>
      <form className="si-form" onSubmit={handleSubmit}>
        <span className="si-eyebrow">Sign in</span>
        <h1 className="si-title">
          Welcome <em>back.</em>
        </h1>
        <p className="si-sub">One sign-in for organizers and administrators.</p>

        <label className="si-label" htmlFor="email">
          Email address
        </label>
        <input
          id="email"
          className="si-input"
          type="email"
          name="email"
          autoComplete="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="you@example.com"
          required
        />

        <label className="si-label" htmlFor="password">
          Password
        </label>
        <input
          id="password"
          className="si-input"
          type="password"
          name="password"
          autoComplete="current-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          required
        />

        <div className="si-row">
          <label className="si-check">
            <input
              type="checkbox"
              checked={remember}
              onChange={(event) => setRemember(event.target.checked)}
            />
            <span>Keep me signed in</span>
          </label>
          <button
            className="si-link si-link-button"
            type="button"
            onClick={() =>
              setError("Password reset is not available yet. Contact the FindOpp team.")
            }
          >
            Forgot your password?
          </button>
        </div>

        {error ? (
          <div className="si-note si-note--error" role="alert">
            {error}
          </div>
        ) : notice ? (
          <div className="si-note si-note--success" role="status">
            {notice}
          </div>
        ) : (
          <div className="si-note">
            <strong>Your role is recognized automatically after sign-in.</strong>
            <span>You will continue to your FindOpp account.</span>
          </div>
        )}

        <button className="si-btn" type="submit" disabled={loading}>
          {loading ? "Signing in..." : "Sign in"}
        </button>

        <a className="si-create" href="/register/">
          Create an organizer account
        </a>
        <p className="si-foot">
          Visitors can browse FindOpp freely, without an account.
        </p>
      </form>
    </AuthLayout>
  );
}
