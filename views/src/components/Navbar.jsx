import { COLORS } from "../constants/theme";

const TABS = [
  { key: "dashboard",  label: "Dashboarding" },
  { key: "resultados", label: "Resultados"   },
  { key: "historico",  label: "Histórico"    },
];

export default function Navbar({ activeTab, onTabChange }) {
  return (
    <nav
      style={{
        background: COLORS.navy,
        display: "flex",
        alignItems: "center",
        padding: "0 32px",
        height: 60,
        gap: 48,
      }}
    >
      <Logo />

      <div style={{ display: "flex", flex: 1, justifyContent: "center" }}>
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => onTabChange(t.key)}
            style={{
              padding: "18px 24px",
              color: activeTab === t.key ? COLORS.white : "rgba(255,255,255,0.65)",
              fontWeight: activeTab === t.key ? 700 : 500,
              fontSize: 15,
              cursor: "pointer",
              borderTop: "3px solid transparent",
              borderLeft: "none",
              borderRight: "none",
              borderBottom: activeTab === t.key ? `3px solid ${COLORS.orange}` : "3px solid transparent",
              transition: "all .2s",
              letterSpacing: ".01em",
              background: "none",
            }}
          >
            {t.label}
          </button>
        ))}
      </div>
    </nav>
  );
}

function Logo() {
  return (
    <img
      src="/atvosp.webp"
      alt="Atvos"
      style={{ height: 40, width: "auto", display: "block" }}
    />
  );
}
