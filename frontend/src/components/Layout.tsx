import { NavLink, Outlet, useNavigate } from "react-router-dom";

export default function Layout() {
  const navigate = useNavigate();

  function logout() {
    localStorage.removeItem("access_token");
    navigate("/login");
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="logo">🏠 ImmoFinder</div>
        <nav>
          <NavLink to="/" end>
            Übersicht
          </NavLink>
          <NavLink to="/favorites">Favoriten</NavLink>
          <NavLink to="/statistics">Statistiken</NavLink>
          <NavLink to="/profile">Suchprofil</NavLink>
          <NavLink to="/notifications">Benachrichtigungen</NavLink>
        </nav>
        <button className="btn-secondary" onClick={logout}>
          Abmelden
        </button>
      </header>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
