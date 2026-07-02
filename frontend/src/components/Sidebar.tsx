import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import SidebarIcon from "./SidebarIcon";

interface SidebarProps {
  open: boolean;
  onToggle: () => void;
}

const navItems = [
  { to: "/budget", label: "Budget", icon: "💰" },
  { to: "/investments", label: "Investments", icon: "📈" },
  { to: "/fire", label: "FIRE", icon: "🔥" },
];

export default function Sidebar({ open, onToggle }: SidebarProps) {
  const [backendStatus, setBackendStatus] = useState("checking");

  useEffect(() => {
    fetch("/api/health")
      .then((response) => response.json())
      .then((body) => setBackendStatus(body.status))
      .catch(() => setBackendStatus("unreachable"));
  }, []);

  const dotClass = backendStatus === "ok" ? "up" : backendStatus === "checking" ? "" : "down";

  return (
    <aside className={`sidebar${open ? "" : " collapsed"}`}>
      <div className="sidebar-header">
        <h1 className="brand">Ignite</h1>
        <button className="icon-btn" aria-label="Collapse sidebar" onClick={onToggle}>
          <SidebarIcon />
        </button>
      </div>
      <nav className="nav">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}
          >
            <span className="nav-icon">{item.icon}</span>
            <span className="nav-label">{item.label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="sidebar-footer">
        <span className={`status-dot ${dotClass}`} />
        <span className="status-text">backend: {backendStatus}</span>
      </div>
    </aside>
  );
}
