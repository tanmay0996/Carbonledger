import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export default function Nav() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <aside className="sidebar">
      <div className="logo">CarbonLedger</div>
      <nav>
        <NavLink to="/" end className={({ isActive }) => isActive ? 'active' : ''}>Dashboard</NavLink>
        <NavLink to="/ingest" className={({ isActive }) => isActive ? 'active' : ''}>Ingest</NavLink>
        <NavLink to="/review" className={({ isActive }) => isActive ? 'active' : ''}>Review</NavLink>
      </nav>
      <button className="logout-btn" onClick={handleLogout}>
        {user?.username} — Logout
      </button>
    </aside>
  )
}
