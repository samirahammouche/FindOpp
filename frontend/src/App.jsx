import SignIn from "./pages/signIn.jsx";
import SignUp from "./pages/signUp.jsx";

export default function App() {
  return window.location.pathname.startsWith("/register") ? <SignUp /> : <SignIn />;
}