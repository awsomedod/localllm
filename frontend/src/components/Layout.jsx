import { NavLink, Outlet, useLocation } from 'react-router-dom'

export default function Layout() {
  const { pathname } = useLocation()
  const membersOn = pathname === '/' || pathname.startsWith('/members/')
  const votesOn = pathname.startsWith('/votes')

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-kicker">Local Congress</span>
          <strong>118th Congress</strong>
        </div>
        <nav>
          <NavLink to="/" className={() => (membersOn ? 'active' : undefined)}>
            Members
          </NavLink>
          <NavLink to="/votes" className={() => (votesOn ? 'active' : undefined)}>
            House votes
          </NavLink>
        </nav>
      </header>
      <main>
        <Outlet />
      </main>
    </div>
  )
}
