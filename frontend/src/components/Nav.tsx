import { NavLink } from 'react-router-dom'
import './Nav.css'

export default function Nav() {
  return (
    <nav className="am-nav">
      <NavLink to="/about" className="am-nav__brand">
        Aaron's Meadow
      </NavLink>
      <NavLink
        to="/"
        end
        className={({ isActive }) => `am-nav__link ${isActive ? 'am-nav__link--active' : ''}`}
      >
        Workbench
      </NavLink>
    </nav>
  )
}
