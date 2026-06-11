import { COLORS } from "../constants/theme";
import { UNIDADES, PROCESSOS, INSUMOS } from "../constants/mockData";

const FILTERS = [
  { key: "unidade",  label: "Unidade Industrial",  options: UNIDADES  },
  { key: "processo", label: "Processo Agronômico",  options: PROCESSOS },
  { key: "insumo",   label: "Tipo de Insumo",       options: INSUMOS   },
];

export default function FilterBar({ filters, onChange, onSearch, onClear }) {
  return (
    <div
      style={{
        background: COLORS.orange,
        borderRadius: 14,
        padding: "20px 24px",
        marginBottom: 24,
      }}
    >
      <div style={{ color: COLORS.white, fontWeight: 800, fontSize: 17, marginBottom: 14 }}>
        Filtrar Resultados
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr 1fr auto auto",
          gap: 12,
          alignItems: "flex-end",
        }}
      >
        {FILTERS.map(({ key, label, options }) => (
          <div key={key}>
            <label
              htmlFor={`filter-${key}`}
              style={{ display: "block", fontSize: 12, fontWeight: 600, color: "rgba(255,255,255,.85)", marginBottom: 6 }}
            >
              {label}
            </label>
            <select
              id={`filter-${key}`}
              value={filters[key]}
              onChange={(e) => onChange(key, e.target.value)}
              style={{
                width: "100%",
                padding: "10px 14px",
                borderRadius: 8,
                border: "none",
                background: COLORS.white,
                color: filters[key] ? COLORS.gray800 : COLORS.gray600,
                fontSize: 13,
                cursor: "pointer",
                outline: "none",
              }}
            >
              <option value="">Selecione</option>
              {options.map((opt) => (
                <option key={opt} value={opt}>{opt}</option>
              ))}
            </select>
          </div>
        ))}

        <button
          onClick={onClear}
          style={actionBtn()}
        >
          Limpar
        </button>

        <button
          onClick={onSearch}
          style={{ ...actionBtn(), display: "flex", alignItems: "center", gap: 6 }}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <circle cx="11" cy="11" r="8" stroke="white" strokeWidth="2" />
            <path d="M21 21l-4.35-4.35" stroke="white" strokeWidth="2" />
          </svg>
          Buscar
        </button>
      </div>
    </div>
  );
}

function actionBtn() {
  return {
    padding: "10px 20px",
    borderRadius: 8,
    background: COLORS.navy,
    color: COLORS.white,
    border: "none",
    fontWeight: 700,
    fontSize: 13,
    cursor: "pointer",
    height: 40,
    alignSelf: "flex-end",
    whiteSpace: "nowrap",
  };
}
