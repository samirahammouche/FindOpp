import { api } from "./client";

// Paths match backend/auth-service/accounts/urls.py (trailing slash required by Django)
const LOGIN = "/api/auth/login/";
const REGISTER = "/api/auth/register/";

export const login = (email, password) =>
  api(LOGIN, { method: "POST", body: { email, password } });

// formData: organization_name, organization_type, city, website, email,
// password, official_document
export const registerOrganizer = (formData) =>
  api(REGISTER, { method: "POST", body: formData });