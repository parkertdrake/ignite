import { useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import SidebarIcon from "./components/SidebarIcon";
import Budget from "./pages/Budget";
import BudgetDetail from "./pages/BudgetDetail";
import Fire from "./pages/Fire";
import Investments from "./pages/Investments";

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const toggleSidebar = () => setSidebarOpen((open) => !open);

  return (
    <div className="app-shell">
      <Sidebar open={sidebarOpen} onToggle={toggleSidebar} />
      <div className="content">
        {/* Toggle lives in the sidebar header while open; the main header
            only shows it once the sidebar is collapsed — never both. */}
        {!sidebarOpen && (
          <header className="topbar">
            <button className="icon-btn" aria-label="Open sidebar" onClick={toggleSidebar}>
              <SidebarIcon />
            </button>
            <h1 className="brand">Ignite</h1>
          </header>
        )}
        <main className="page">
          <Routes>
            <Route path="/" element={<Navigate to="/budget" replace />} />
            <Route path="/budget" element={<Budget />} />
            <Route path="/budget/:budgetId" element={<BudgetDetail />} />
            <Route path="/investments" element={<Investments />} />
            <Route path="/fire" element={<Fire />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}
