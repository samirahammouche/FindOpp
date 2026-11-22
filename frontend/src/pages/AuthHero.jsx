import "./SignIn.css";

// Put your photo at frontend/public/images/signin-hero.jpg
const HERO_IMAGE = "/images/signin-hero.jpg";

export default function AuthHero() {
  return (
    <aside className="si-hero" style={{ backgroundImage: `url(${HERO_IMAGE})` }}>
      <div className="si-hero__shade" />
      <div className="si-brand">
        <span className="si-brand__mark">F</span>
        <span className="si-brand__name">Find<strong>Opp</strong>.</span>
      </div>
      <p className="si-hero__tag">Professional access</p>
      <span className="si-hero__badge" aria-hidden="true">
        <svg viewBox="0 0 24 24" width="30" height="30" fill="none" stroke="#fff" strokeWidth="1.4" strokeLinejoin="round" strokeLinecap="round">
          <path d="M12 4 2 9l10 5 10-5-10-5Z" />
          <path d="M6 11.5V16c0 1.2 2.7 2.5 6 2.5s6-1.3 6-2.5v-4.5" />
          <path d="M22 9v5" />
        </svg>
      </span>
      <blockquote className="si-hero__quote">“Great ideas<br />start<br />with you.”</blockquote>
      <p className="si-hero__foot">FindOpp · Ideas, connections, opportunities.</p>
    </aside>
  );
}