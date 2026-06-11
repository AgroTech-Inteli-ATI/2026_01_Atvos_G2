import { useState } from "react";
import { COLORS } from "./constants/theme";
import Navbar from "./components/Navbar";
import Dashboard from "./pages/Dashboard";
import Resultados from "./pages/Resultados";
import Historico from "./pages/Historico";

export default function App() {
  const [activeTab, setActiveTab] = useState("resultados");

  return (
    <div
      style={{
        fontFamily: "'DM Sans', 'Nunito', sans-serif",
        background: COLORS.gray50,
        minHeight: "100vh",
        color: COLORS.gray800,
      }}
    >
      <Navbar activeTab={activeTab} onTabChange={setActiveTab} />

      {activeTab === "dashboard"  && <Dashboard />}
      {activeTab === "resultados" && <Resultados />}
      {activeTab === "historico"  && <Historico />}
    </div>
  );
}
