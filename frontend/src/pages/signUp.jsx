import { useState } from "react";
import AuthLayout from "../AuthLayout.jsx";
import { readApiResponse } from "../api.js";
import "../auth.css";

export default function SignUp() {
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [fileName, setFileName] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const formData = new FormData(event.currentTarget);
      const response = await fetch("/api/auth/register/", {
        method: "POST",
        body: formData,
      });
      await readApiResponse(
        response,
        "We could not create your account. Check the form and try again.",
      );
      setSubmitted(true);
    } catch (submitError) {
      setError(
        submitError instanceof Error
          ? submitError.message
          : "Unable to create your account. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout>
      <form
        className="si-form si-form--signup"
        onSubmit={handleSubmit}
        encType="multipart/form-data"
      >
        <span className="si-eyebrow">Organizer sign up</span>
        <h1 className="si-title si-title--signup">
          Create your
          <br />
          organizer <em>account.</em>
        </h1>
        <p className="si-sub si-sub--signup">
          Share your opportunities with the right people.
        </p>

        {submitted ? (
          <div className="si-submission" role="status">
            <strong>Your application has been submitted.</strong>
            <span>
              Our team will review your organization details and supporting
              document. You can sign in after your account is approved.
            </span>
            <a className="si-create" href="/">
              Return to sign in
            </a>
          </div>
        ) : (
          <>
            <label className="si-label" htmlFor="organization-name">
              Organization name
            </label>
            <input
              id="organization-name"
              className="si-input"
              type="text"
              name="organization_name"
              autoComplete="organization"
              maxLength={200}
              placeholder="Algeria Startup Hub"
              required
            />

            <div className="si-grid">
              <div>
                <label className="si-label" htmlFor="first-name">
                  Your first name
                </label>
                <input
                  id="first-name"
                  className="si-input"
                  type="text"
                  name="first_name"
                  autoComplete="given-name"
                  maxLength={100}
                  required
                />
              </div>
              <div>
                <label className="si-label" htmlFor="last-name">
                  Your last name
                </label>
                <input
                  id="last-name"
                  className="si-input"
                  type="text"
                  name="last_name"
                  autoComplete="family-name"
                  maxLength={100}
                  required
                />
              </div>
            </div>

            <div className="si-grid">
              <div>
                <label className="si-label" htmlFor="organization-type">
                  Organization type
                </label>
                <select
                  id="organization-type"
                  className="si-input si-select"
                  name="organization_type"
                  defaultValue=""
                  required
                >
                  <option value="" disabled>
                    Select a type
                  </option>
                  <option value="UNIVERSITY">University</option>
                  <option value="COMPANY">Company</option>
                  <option value="NGO">NGO</option>
                  <option value="CLUB">Club</option>
                </select>
                <span className="si-hint">University · Company · NGO · Club</span>
              </div>
              <div>
                <label className="si-label" htmlFor="city">
                  City
                </label>
                <input
                  id="city"
                  className="si-input"
                  type="text"
                  name="city"
                  autoComplete="address-level2"
                  maxLength={100}
                  placeholder="Alger"
                  required
                />
              </div>
            </div>

            <label className="si-label" htmlFor="website">
              Website
            </label>
            <input
              id="website"
              className="si-input"
              type="url"
              name="website"
              autoComplete="url"
              maxLength={255}
              placeholder="https://yourorganization.example"
              required
            />

            <label className="si-label" htmlFor="email">
              Work email address
            </label>
            <input
              id="email"
              className="si-input"
              type="email"
              name="email"
              autoComplete="email"
              placeholder="contact@example.com"
              required
            />

            <label className="si-label" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              className="si-input si-input--last"
              type="password"
              name="password"
              autoComplete="new-password"
              minLength={8}
              required
            />
            <span className="si-hint si-hint--password">
              Use at least 8 characters and avoid common passwords.
            </span>

            <label className="si-label" htmlFor="official-document">
              Official document
            </label>
            <label className="si-upload" htmlFor="official-document">
              <input
                id="official-document"
                type="file"
                name="official_document"
                accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg"
                onChange={(event) =>
                  setFileName(event.target.files?.[0]?.name || "")
                }
                required
              />
              <span className="si-upload__icon" aria-hidden="true">
                <svg
                  viewBox="0 0 24 24"
                  width="22"
                  height="22"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.7"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <path d="M14 2v6h6M8 13h8M8 17h8M8 9h1" />
                </svg>
              </span>
              <span className="si-upload__copy">
                <strong>
                  {fileName || "Upload an official supporting document"}
                </strong>
                <small>PDF, PNG or JPG · 10 MB maximum</small>
              </span>
            </label>

            {error && (
              <div className="si-note si-note--error" role="alert">
                {error}
              </div>
            )}

            <div className="si-note si-note--signup">
              Our team will review your account within 48 hours.
            </div>

            <button className="si-btn" type="submit" disabled={loading}>
              {loading ? "Submitting..." : "Create my organizer account"}
            </button>

            <p className="si-terms">
              By continuing, you agree to the terms of use and privacy policy.
            </p>
            <a className="si-create si-create--bottom" href="/">
              Already registered? Sign in
            </a>
          </>
        )}
      </form>
    </AuthLayout>
  );
}
