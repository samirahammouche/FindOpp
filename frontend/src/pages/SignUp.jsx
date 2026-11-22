import { useRef, useState } from "react";
import { Link } from "react-router-dom";
import AuthHero from "./AuthHero";
import { registerOrganizer } from "../api/auth";
import "./SignIn.css";
import "./SignUp.css";

const ORG_TYPES = ["University", "Company", "NGO", "Club"];
const MAX_SIZE = 10 * 1024 * 1024; // 10 MB
const ALLOWED = ["application/pdf", "image/png", "image/jpeg"];

export default function SignUp() {
  const fileRef = useRef(null);
  const [form, setForm] = useState({
    organization_name: "",
    organization_type: "company",
    city: "",
    website: "",
    email: "",
    password: "",
  });
  const [file, setFile] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value });

  function handleFile(e) {
    const f = e.target.files[0];
    if (!f) return;
    if (!ALLOWED.includes(f.type)) {
      setError("The document must be a PDF, PNG or JPG file.");
      e.target.value = "";
      return;
    }
    if (f.size > MAX_SIZE) {
      setError("The document is larger than 10 MB.");
      e.target.value = "";
      return;
    }
    setError("");
    setFile(f);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");

    if (!form.organization_name || !form.city || !form.website || !form.email) {
      return setError("Fill in the organization name, city, website and email address.");
    }
    if (form.password.length < 8 || !/\d/.test(form.password)) {
      return setError("Your password needs at least 8 characters, including a number.");
    }
    if (!file) return setError("Upload an official supporting document.");

    // The backend needs a full URL, so add https:// if the user left it out
    const website = /^https?:\/\//i.test(form.website) ? form.website : `https://${form.website}`;

    const body = new FormData();
    Object.entries({ ...form, website }).forEach(([k, v]) => body.append(k, v));
    body.append("official_document", file);

    setLoading(true);
    try {
      await registerOrganizer(body);
      setDone(true);
    } catch (err) {
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

        {done ? (
          <div className="si-form">
            <span className="si-eyebrow">Organizer sign up</span>
            <h1 className="si-title">Thank <em>you.</em></h1>
            <p className="si-sub">
              Your account is created. Our team will verify it within 48 hours, and you can sign in once it’s approved.
            </p>
            <Link className="si-btn su-btnlink" to="/login">Go to sign in</Link>
          </div>
        ) : (
          <form className="si-form su-form" onSubmit={handleSubmit} noValidate>
            <span className="si-eyebrow">Organizer sign up</span>
            <h1 className="si-title">Create your<br />organizer <em>account.</em></h1>
            <p className="si-sub">Share your opportunities with the right people.</p>

            <label className="si-label" htmlFor="org">Organization name</label>
            <input id="org" className="si-input" value={form.organization_name} onChange={set("organization_name")} required />

            <div className="su-grid">
              <div className="su-col">
                <label className="si-label" htmlFor="type">Organization type</label>
                <select id="type" className="si-input si-select" value={form.organization_type} onChange={set("organization_type")}>
                  {ORG_TYPES.map((t) => (
                    <option key={t} value={t.toLowerCase()}>{t}</option>
                  ))}
                </select>
                <span className="si-hint">University · Company · NGO · Club</span>
              </div>
              <div className="su-col">
                <label className="si-label" htmlFor="city">City</label>
                <input id="city" className="si-input" value={form.city} onChange={set("city")} required />
              </div>
            </div>

            <label className="si-label" htmlFor="website">Website</label>
            <input id="website" className="si-input" placeholder="https://" value={form.website} onChange={set("website")} required />

            <label className="si-label" htmlFor="email">Work email address</label>
            <input id="email" className="si-input" type="email" autoComplete="email" value={form.email} onChange={set("email")} required />

            <label className="si-label" htmlFor="password">Password</label>
            <input id="password" className="si-input su-tight" type="password" autoComplete="new-password" value={form.password} onChange={set("password")} required />
            <span className="si-hint su-hintgap">At least 8 characters, including a number.</span>

            <span className="si-label">Official document</span>
            <button type="button" className="su-drop" onClick={() => fileRef.current.click()}>
              <span className="su-drop__icon" aria-hidden="true">
                <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="#1e4e8c" strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round">
                  <path d="M3 5.5C5.5 4.5 9 4.5 12 6.5c3-2 6.5-2 9-1V19c-2.5-1-6-1-9 1-3-2-6.5-2-9-1V5.5Z" />
                  <path d="M12 6.5V20" />
                </svg>
              </span>
              <span className="su-drop__text">
                <strong>{file ? file.name : "Upload an official supporting document"}</strong>
                <span>{file ? "Click to replace" : "PDF, PNG or JPG · 10 MB maximum"}</span>
              </span>
            </button>
            <input ref={fileRef} type="file" accept=".pdf,.png,.jpg,.jpeg" onChange={handleFile} hidden />

            {error ? (
              <div className="si-note si-note--error" role="alert">{error}</div>
            ) : (
              <div className="si-note"><strong>Our team will verify your account within 48 hours.</strong></div>
            )}

            <button className="si-btn" type="submit" disabled={loading}>
              {loading ? "Creating account…" : "Create my organizer account"}
            </button>

            <p className="si-foot su-terms">By continuing, you agree to the terms of use and privacy policy.</p>
            <Link className="si-create su-signin" to="/login">Already registered? Sign in</Link>
          </form>
        )}
      </main>
    </div>
  );
}