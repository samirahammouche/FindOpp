import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth, ROLE_HOME } from "../context/AuthContext";
import heroImage from "../assets/screen.png";
import aboutImage from "../assets/Real event photograph (3).png";
import "./Home.css";

/* ------------------------------------------------------------------ */
/* Images: export them from Figma into frontend/public/images/        */
/* Missing images fall back to a plain colour, nothing breaks.        */
/* ------------------------------------------------------------------ */
const IMG = {
  hero: heroImage,
  about: aboutImage,
};

/* ------------------------------------------------------------------ */
/* Static sample data. Replace with calls to /api/events when the     */
/* event service is ready (see the note at the bottom of the file).   */
/* ------------------------------------------------------------------ */
const CATEGORIES = [
  { key: "all", label: "All", icon: "bolt" },
  { key: "hackathon", label: "Hackathons", icon: "code" },
  { key: "scholarship", label: "Scholarships", icon: "cap" },
  { key: "event", label: "Events", icon: "flask" },
  { key: "club", label: "Clubs", icon: "users" },
];
const COUNTS = { all: 2820, hackathon: 840, scholarship: 1020, event: 680, club: 400 };
const TAG = { hackathon: "Hackathon", scholarship: "Scholarship", event: "Event", club: "Student Club" };

const LEVELS = ["Bachelor", "Master", "PhD"];
const FUNDING = [["Full tuition", 180], ["Monthly stipend", 320], ["Partial Grant", 190]];
const REGIONS = [["France", 210], ["Canada", 180], ["United States", 360], ["Remote / Worldwide", 420]];

const LISTINGS = [
  {
    id: 1, category: "hackathon", featured: true, org: "MIT Innovation Labs",
    title: "Annual AI & Robotics Global Hackathon 2025",
    place: "Virtual & Cambridge, MA", reward: "$50,000 Pool", date: "Nov 15 – 17, 2025",
    open: false, levels: ["Bachelor", "Master", "PhD"], funding: null, region: "United States",
    image: "/images/opportunities/hackathon.jpg",
  },
  {
    id: 2, category: "scholarship", org: "Sorbonne & Paris Foundation",
    title: "Applied AI & Sciences Academic Excellence Grant",
    place: "Paris, France", reward: "Full Tuition + $2,000/mo", date: "Oct 20, 2025",
    open: false, levels: ["Master", "PhD"], funding: "Full tuition", region: "France",
    image: "/images/opportunities/scholarship.jpg",
  },
  {
    id: 3, category: "event", org: "Paris Research Institute",
    title: "Women in Data Science Summit 2026",
    place: "Berlin, Germany", reward: "Free + travel grants", date: "Jan 14, 2027",
    open: true, levels: ["Bachelor", "Master"], funding: "Partial Grant", region: "Germany",
    image: "/images/opportunities/event.jpg",
  },
  {
    id: 4, category: "club", org: "Global Tech Leadership Council",
    title: "Executive Student Board & Fellowship 2025–2026",
    place: "Worldwide (Remote)", reward: "$4,000 Project Budget", date: "Oct 03, 2025",
    open: false, levels: ["Bachelor"], funding: "Monthly stipend", region: "Remote / Worldwide",
    image: "/images/opportunities/club.jpg",
  },
];

const OFFERS = [
  { icon: "code", title: "Hackathons", cat: "hackathon", link: "Explore Events",
    text: "Build projects in 48-hour sprints, collaborate with multidisciplinary peers, and win grand cash prizes." },
  { icon: "users", title: "Student Clubs", cat: "club", link: "Explore Clubs",
    text: "Find executive boards, special interest societies, and student associations across campus chapters." },
  { icon: "cap", title: "Scholarships & Grants", cat: "scholarship", link: "Explore Grants",
    text: "Access merit and financial need academic stipends, and fully-funded corporate grants." },
  { icon: "flask", title: "Events & Conferences", cat: "event", link: "Explore Internships",
    text: "Gain practical industry work experience, research fellowships, and mentorship from lead scientists." },
];

const FEATURES = [
  { icon: "shield", title: "Direct Access to Verified Portals",
    text: "Skip wall-of-data job boards. Every listing is verified directly by universities and partnering companies." },
  { icon: "bell", title: "Personalized Tracking & Alerts",
    text: "Receive reminders for upcoming application deadlines, scholarship events, and club recruitments." },
  { icon: "bolt", title: "One-Click Applications",
    text: "Apply seamlessly with pre-filled profiles crafted for students and emerging professionals." },
];

const FOOTER_COLS = [
  ["Explore", ["All Opportunities", "Featured", "Student Events", "Upcoming Events"]],
  ["Categories", ["Hackathons", "Scholarships", "Events", "Student Clubs"]],
  ["Company", ["About Us", "Partner With Us", "Careers", "Press"]],
  ["Legal", ["Privacy Policy", "Terms of Service", "Security"]],
];

/* ------------------------------ icons ------------------------------ */
const PATHS = {
  search: <><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></>,
  arrow: <path d="M5 12h14M13 6l6 6-6 6" />,
  out: <path d="M7 17 17 7M8 7h9v9" />,
  bookmark: <path d="M6 4h12v17l-6-4-6 4V4Z" />,
  check: <path d="m5 12 5 5 9-10" />,
  pin: <><path d="M12 21s7-6.2 7-11a7 7 0 1 0-14 0c0 4.8 7 11 7 11Z" /><circle cx="12" cy="10" r="2.5" /></>,
  calendar: <><rect x="4" y="5" width="16" height="15" rx="2" /><path d="M4 10h16M9 3v4M15 3v4" /></>,
  coin: <><circle cx="12" cy="12" r="8" /><path d="M12 7.5v9M9.5 10.2c0-1 1-1.7 2.5-1.7s2.5.7 2.5 1.7-1 1.4-2.5 1.6-2.5.7-2.5 1.7 1 1.7 2.5 1.7 2.5-.7 2.5-1.7" /></>,
  code: <path d="m8 8-4 4 4 4M16 8l4 4-4 4M14 5l-4 14" />,
  cap: <><path d="M12 4 2 9l10 5 10-5-10-5Z" /><path d="M6 11.5V16c0 1.2 2.7 2.5 6 2.5s6-1.3 6-2.5v-4.5M22 9v5" /></>,
  users: <><circle cx="9" cy="8" r="3" /><path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6M16 5a3 3 0 0 1 0 6M18 14c2 .6 3 2.4 3 6" /></>,
  flask: <path d="M9 3h6M10 3v6l-5 9a2 2 0 0 0 2 3h10a2 2 0 0 0 2-3l-5-9V3" />,
  shield: <><path d="M12 3 4 6v6c0 4.5 3.2 7.5 8 9 4.8-1.5 8-4.5 8-9V6l-8-3Z" /><path d="m9 12 2 2 4-4" /></>,
  bell: <path d="M6 16v-5a6 6 0 1 1 12 0v5l2 2H4l2-2ZM10 21h4" />,
  bolt: <path d="M13 3 5 14h6l-1 7 8-11h-6l1-7Z" />,
  close: <path d="M6 6l12 12M18 6 6 18" />,
  chevron: <path d="m6 9 6 6 6-6" />,
};
function Ico({ n, size = 16 }) {
  return (
    <svg className="hm-ico" width={size} height={size} viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {PATHS[n]}
    </svg>
  );
}

const toggle = (setter, value) =>
  setter((cur) => (cur.includes(value) ? cur.filter((x) => x !== value) : [...cur, value]));
const scrollToList = () =>
  document.getElementById("opportunities")?.scrollIntoView({ behavior: "smooth" });

export default function Home() {
  const { user } = useAuth();
  const space = user ? ROLE_HOME[user.role] || "/" : "/login";

  const [heroQuery, setHeroQuery] = useState("");
  const [heroType, setHeroType] = useState("all");
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("all");
  const [levels, setLevels] = useState([]);
  const [funding, setFunding] = useState([]);
  const [regions, setRegions] = useState([]);
  const [saved, setSaved] = useState([]);
  const [page, setPage] = useState(1);

  const TOTAL_PAGES = 69; // from the API later

  function explore(e) {
    e.preventDefault();
    setQuery(heroQuery);
    setCategory(heroType);
    setPage(1);
    scrollToList();
  }
  function pickCategory(key) {
    setCategory(key);
    setPage(1);
    scrollToList();
  }

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    return LISTINGS.filter(
      (l) =>
        (category === "all" || l.category === category) &&
        (!q || `${l.title} ${l.org}`.toLowerCase().includes(q)) &&
        (!levels.length || l.levels.some((x) => levels.includes(x))) &&
        (!funding.length || funding.includes(l.funding)) &&
        (!regions.length || regions.includes(l.region))
    );
  }, [query, category, levels, funding, regions]);

  const activeFilters = [
    ...levels.map((v) => ({ label: v, remove: () => toggle(setLevels, v) })),
    ...funding.map((v) => ({ label: v, remove: () => toggle(setFunding, v) })),
    ...regions.map((v) => ({ label: v, remove: () => toggle(setRegions, v) })),
  ];
  const clearAll = () => { setLevels([]); setFunding([]); setRegions([]); };

  return (
    <div className="home">
      {/* ---------- Navbar ---------- */}
      <header className="hm-nav">
        <div className="hm-wrap hm-nav__in">
          <Link to="/" className="hm-brand">
            <span className="hm-brand__mark">F</span>
            <span>Find<strong>Opp</strong>.</span>
          </Link>
          <nav className="hm-nav__links" aria-label="Main">
            <a href="#about">About</a>
            <a href="#categories">Categories</a>
            <a href="#opportunities">Opportunities</a>
            <a href="#contact">Contact</a>
          </nav>
          <Link to={space} className="hm-btn hm-btn--navy">
            Organizer Space <Ico n="arrow" size={13} />
          </Link>
        </div>
      </header>

      {/* ---------- Hero ---------- */}
      <section className="hm-hero" style={{ "--img": `url(${IMG.hero})` }}>
        <div className="hm-wrap hm-hero__in">
          <h1>Discover Your Next <br />Opportunity</h1>
          <p>Explore top hackathons, campus clubs, exclusive scholarships, research internships, and career programs all in one unified ecosystem.</p>

          <form className="hm-search" onSubmit={explore}>
            <Ico n="search" size={18} />
            <input
              value={heroQuery}
              onChange={(e) => setHeroQuery(e.target.value)}
              placeholder="Search events, clubs, scholarships, internships..."
              aria-label="Search opportunities"
            />
            <span className="hm-search__sep" />
            <label className="hm-select">
              <select value={heroType} onChange={(e) => setHeroType(e.target.value)} aria-label="Type">
                <option value="all">All Types</option>
                {CATEGORIES.slice(1).map((c) => <option key={c.key} value={c.key}>{c.label}</option>)}
              </select>
              <Ico n="chevron" size={12} />
            </label>
            <button className="hm-btn hm-btn--lilac" type="submit">Explore <Ico n="arrow" size={13} /></button>
          </form>

          <div className="hm-chips">
            {[["code", "Hackathons", "hackathon"], ["cap", "Scholarships & Grants", "scholarship"],
              ["flask", "Events & Conferences", "event"], ["users", "Student Clubs", "club"]].map(([icon, label, key]) => (
              <button key={key} type="button" className="hm-chip" onClick={() => pickCategory(key)}>
                <Ico n={icon} size={13} /> {label}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* ---------- About ---------- */}
      <section className="hm-about" id="about">
        <div className="hm-wrap hm-about__grid">
          <div>
            <span className="hm-tag"><Ico n="cap" size={12} /> ABOUT FINDOPP</span>
            <h2 className="hm-h2">We bridge the gap to <em>your future.</em></h2>
            <p className="hm-lead">Life-changing opportunities, brought closer.</p>
            <p className="hm-muted">FindOpp was built on a simple premise: life-changing opportunities shouldn’t be scattered, opaque, or locked away. We bring on-campus organizations, cutting-edge hackathons, and high-impact fellowships into one seamless experience.</p>
            <ul className="hm-features">
              {FEATURES.map((f) => (
                <li key={f.title}>
                  <span className="hm-feat__ico"><Ico n={f.icon} size={18} /></span>
                  <div><strong>{f.title}</strong><p>{f.text}</p></div>
                </li>
              ))}
            </ul>
          </div>

          <div className="hm-about__media">
            <span className="hm-orb"><Ico n="cap" size={16} /></span>
            <div className="hm-about__img" style={{ backgroundImage: `url(${IMG.about})` }} role="img" aria-label="Students studying together" />
            <div className="hm-float hm-float--top">
              <span className="hm-float__check"><Ico n="check" size={14} /></span>
              <div><strong>98% verified</strong><small>Find out more with confidence</small></div>
            </div>
            <div className="hm-float hm-float--join">
              <span className="hm-float__ico"><Ico n="cap" size={18} /></span>
              <div><strong>Join 45k+ Active Students</strong><small>Continuing from your partnered colleges worldwide.</small></div>
            </div>
          </div>
        </div>
      </section>

      {/* ---------- What we offer ---------- */}
      <section className="hm-offer" id="categories">
        <div className="hm-wrap">
          <h2 className="hm-center">What We Offer</h2>
          <p className="hm-center hm-muted">Tailored pathways for every phase of your university and post-graduate journey.</p>
          <div className="hm-offer__grid">
            {OFFERS.map((o) => (
              <article key={o.title} className="hm-offer__card">
                <span className="hm-offer__ring"><Ico n={o.icon} size={34} /></span>
                <h3>{o.title}</h3>
                <p>{o.text}</p>
                <button type="button" className="hm-link" onClick={() => pickCategory(o.cat)}>
                  {o.link} <Ico n="arrow" size={13} />
                </button>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* ---------- Latest opportunities ---------- */}
      <section className="hm-latest" id="opportunities">
        <div className="hm-wrap">
          <div className="hm-latest__head">
            <div>
              <span className="hm-tag hm-tag--plain"><Ico n="bolt" size={12} /> FIND YOUR NEXT</span>
              <h2 className="hm-h2">Latest <em>Opportunities</em></h2>
              <p className="hm-muted">Explore {COUNTS.all.toLocaleString()} verified hackathons, scholarships, events and student clubs.</p>
            </div>
            <label className="hm-field">
              <Ico n="search" size={15} />
              <input value={query} onChange={(e) => { setQuery(e.target.value); setPage(1); }}
                placeholder="Search by keyword or organization..." />
            </label>
          </div>

          <div className="hm-tabs" role="tablist">
            {CATEGORIES.map((c) => (
              <button key={c.key} role="tab" aria-selected={category === c.key}
                className={`hm-tab hm-tab--${c.key} ${category === c.key ? "is-on" : ""}`}
                onClick={() => { setCategory(c.key); setPage(1); }}>
                <Ico n={c.icon} size={14} /> {c.label} <b>{COUNTS[c.key].toLocaleString()}</b>
              </button>
            ))}
          </div>

          <div className="hm-active">
            <span>Active filters:</span>
            {activeFilters.length === 0 && <em className="hm-muted">none</em>}
            {activeFilters.map((f) => (
              <button key={f.label} className="hm-pill" onClick={f.remove}>{f.label} <Ico n="close" size={10} /></button>
            ))}
            {activeFilters.length > 0 && <button className="hm-clear" onClick={clearAll}>Clear all</button>}
            <small>Archived listings · original dates retained</small>
          </div>

          <div className="hm-latest__grid">
            <aside className="hm-side">
              <div className="hm-side__box">
                <h4>Refine your search</h4>

                <p className="hm-side__label">Study level</p>
                <div className="hm-side__chips">
                  {LEVELS.map((l) => (
                    <button key={l} className={`hm-pill ${levels.includes(l) ? "is-on" : ""}`}
                      onClick={() => toggle(setLevels, l)}>{l}</button>
                  ))}
                </div>

                <p className="hm-side__label">Funding</p>
                {FUNDING.map(([name, n]) => (
                  <label key={name} className="hm-check">
                    <input type="checkbox" checked={funding.includes(name)} onChange={() => toggle(setFunding, name)} />
                    <span>{name}</span><small>{n}</small>
                  </label>
                ))}

                <p className="hm-side__label">Region</p>
                {REGIONS.map(([name, n]) => (
                  <label key={name} className="hm-check">
                    <input type="checkbox" checked={regions.includes(name)} onChange={() => toggle(setRegions, name)} />
                    <span>{name}</span><small>{n}</small>
                  </label>
                ))}
              </div>

              <div className="hm-alert">
                <small>STAY ONE STEP AHEAD</small>
                <h4>Create an alert</h4>
                <p>Your next opportunity, straight to your inbox.</p>
                <Link to="/register" className="hm-btn hm-btn--lilac">Create an alert</Link>
              </div>
            </aside>

            <div>
              <div className="hm-list">
                {visible.length === 0 && <p className="hm-empty">No opportunities match your search yet.</p>}
                {visible.map((l) => (
                  <article key={l.id} className={`hm-card ${l.featured ? "hm-card--featured" : ""}`}>
                    {l.featured && <div className="hm-card__badge">★ FEATURED</div>}
                    <div className="hm-card__row">
                      <div className="hm-card__thumb" style={{ backgroundImage: `url(${l.image})` }} />
                      <div className="hm-card__main">
                        <div className="hm-card__top">
                          <span className={`hm-kind hm-kind--${l.category}`}>{TAG[l.category]}</span>
                          <span className="hm-org">{l.org} <Ico n="check" size={11} /></span>
                        </div>
                        <h3>{l.title}</h3>
                        <div className="hm-meta">
                          <span><Ico n="pin" size={12} /> {l.place}</span>
                          <span className="hm-meta--money"><Ico n="coin" size={12} /> {l.reward}</span>
                          <span><Ico n="calendar" size={12} /> {l.date}</span>
                        </div>
                      </div>
                      <div className="hm-card__side">
                        <button className={`hm-save ${saved.includes(l.id) ? "is-on" : ""}`}
                          aria-label="Save" aria-pressed={saved.includes(l.id)}
                          onClick={() => toggle(setSaved, l.id)}><Ico n="bookmark" size={16} /></button>
                        <div className="hm-card__status">
                          {l.open
                            ? <><strong>Applications open</strong><small>{l.date}</small></>
                            : <><strong className="hm-late">0 days left</strong><small>Applications closed</small></>}
                        </div>
                        <Link to={`/events/${l.id}`} className="hm-btn hm-btn--navy">View opportunity <Ico n="out" size={12} /></Link>
                      </div>
                    </div>
                  </article>
                ))}
              </div>

              <div className="hm-pager">
                <small>Showing 1–{visible.length} of {COUNTS.all.toLocaleString()} opportunities</small>
                <div>
                  <button disabled={page === 1} onClick={() => setPage(page - 1)}>Previous</button>
                  {[1, 2, 3].map((n) => (
                    <button key={n} className={page === n ? "is-on" : ""} onClick={() => setPage(n)}>{n}</button>
                  ))}
                  <span>…</span>
                  <button className={page === TOTAL_PAGES ? "is-on" : ""} onClick={() => setPage(TOTAL_PAGES)}>{TOTAL_PAGES}</button>
                  <button disabled={page === TOTAL_PAGES} onClick={() => setPage(page + 1)}>Next</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ---------- Call to action ---------- */}
      <section className="hm-cta">
        <div className="hm-wrap">
          <h2>Make your next move count.</h2>
          <p>Your next life-changing conference keynote, inspiring hackathon, or fully-funded global scholarship is just one discovery away.</p>
          <div className="hm-cta__btns">
            <button className="hm-btn hm-btn--white" onClick={scrollToList}>START EXPLORING NOW <Ico n="out" size={12} /></button>
            <Link to="/register" className="hm-btn hm-btn--ghost">POST AN OPPORTUNITY <Ico n="out" size={12} /></Link>
          </div>
        </div>
      </section>

      {/* ---------- Footer ---------- */}
      <footer className="hm-footer" id="contact">
        <div className="hm-wrap hm-footer__grid">
          <div>
            <Link to="/" className="hm-brand hm-brand--light">
              <span className="hm-brand__mark">F</span><span>Find<strong>Opp</strong>.</span>
            </Link>
            <p>Empowering university students to discover curated hackathons, scholarships, events and student clubs in Algeria and worldwide.</p>
          </div>
          {FOOTER_COLS.map(([title, links]) => (
            <div key={title}>
              <h5>{title}</h5>
              <ul>{links.map((l) => <li key={l}><a href="#opportunities">{l}</a></li>)}</ul>
            </div>
          ))}
        </div>
        <div className="hm-wrap hm-footer__bar">
          <small>© 2026 FindOpp Inc. Built for ambitious university minds.</small>
          <small>CURATED OPPORTUNITIES WORLDWIDE · ALGERIA & GLOBAL</small>
        </div>
      </footer>
    </div>
  );
}

/*
  Connecting to the event service later:
  - fetch `/api/events?search=&category=&page=` with api() from "../api/client"
    inside a useEffect, and replace LISTINGS / COUNTS / TOTAL_PAGES with the response.
  - The "View opportunity" button already links to /events/:id.
*/
