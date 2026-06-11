import { COLORS } from "../constants/theme";

export default function Pagination({ page, totalPages, totalItems, itemsPerPage, onPageChange }) {
  const from = (page - 1) * itemsPerPage + 1;
  const to   = Math.min(page * itemsPerPage, totalItems);

  // Janela deslizante de 5 páginas centrada na página atual
  const WINDOW = 5;
  let start = Math.max(1, page - Math.floor(WINDOW / 2));
  let end   = start + WINDOW - 1;
  if (end > totalPages) {
    end   = totalPages;
    start = Math.max(1, end - WINDOW + 1);
  }
  const pages = Array.from({ length: end - start + 1 }, (_, i) => start + i);

  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: 20 }}>
      <span style={{ fontSize: 13, color: COLORS.gray600 }}>
        Exibindo {from} a {to} de {totalItems} registros
      </span>

      <div style={{ display: "flex", gap: 6 }}>
        <button
          onClick={() => onPageChange(page - 1)}
          disabled={page === 1}
          style={btnStyle(false, page === 1)}
        >
          Anterior
        </button>

        {pages.map((p) => (
          <button
            key={p}
            onClick={() => onPageChange(p)}
            style={btnStyle(p === page, false)}
          >
            {p}
          </button>
        ))}

        <button
          onClick={() => onPageChange(page + 1)}
          disabled={page === totalPages}
          style={btnStyle(false, page === totalPages)}
        >
          Próxima
        </button>
      </div>
    </div>
  );
}

function btnStyle(active, disabled) {
  return {
    padding: "6px 14px",
    borderRadius: 8,
    border: `1px solid ${active ? COLORS.navy : COLORS.gray200}`,
    background: active ? COLORS.navy : COLORS.white,
    color: active ? COLORS.white : COLORS.gray800,
    fontSize: 13,
    fontWeight: active ? 700 : 500,
    cursor: disabled ? "not-allowed" : "pointer",
    opacity: disabled ? 0.4 : 1,
  };
}
