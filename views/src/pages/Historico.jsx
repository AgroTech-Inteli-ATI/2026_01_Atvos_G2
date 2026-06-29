import { useState } from "react";
import { COLORS } from "../constants/theme";
import { ITEMS_PER_PAGE } from "../constants/mockData";
import Tag from "../components/Tag";
import Pagination from "../components/Pagination";
import { usePipeline } from "../context/PipelineContext";

const COLUMNS = [
  "DATA DE IMPORTAÇÃO",
  "NOME DA LISTA",
  "Nº DE TALHÕES",
  "PROCESSOS AVALIADOS",
  "AÇÕES",
];

export default function Historico() {
  const { historico } = usePipeline();
  const [page, setPage] = useState(1);

  const totalPages = Math.max(1, Math.ceil(historico.length / ITEMS_PER_PAGE));
  const pageRows   = historico.slice((page - 1) * ITEMS_PER_PAGE, page * ITEMS_PER_PAGE);

  return (
    <div style={{ maxWidth: 1280, margin: "0 auto", padding: "32px 24px" }}>
      <div style={{
        background: COLORS.white,
        borderRadius: 12,
        boxShadow: "0 1px 4px rgba(0,0,0,.07)",
        padding: 24,
      }}>
        <h2 style={{ fontSize: 20, fontWeight: 800, color: COLORS.navy, marginBottom: 20 }}>
          Histórico de Importações
        </h2>

        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ background: COLORS.orangeLight }}>
              {COLUMNS.map((h) => (
                <th
                  key={h}
                  style={{
                    padding: "10px 14px", textAlign: "left",
                    fontSize: 11, fontWeight: 700,
                    color: COLORS.orange, letterSpacing: ".06em",
                  }}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pageRows.length === 0 ? (
              <tr>
                <td
                  colSpan={COLUMNS.length}
                  style={{ padding: "48px 0", textAlign: "center", color: COLORS.gray400, fontSize: 14 }}
                >
                  Nenhuma importação registrada. Use "Importar Lista" para começar.
                </td>
              </tr>
            ) : (
              pageRows.map((row, i) => (
                <tr
                  key={i}
                  style={{
                    borderBottom: `1px solid ${COLORS.gray100}`,
                    background: i % 2 === 0 ? COLORS.white : COLORS.gray50,
                  }}
                >
                  <td style={cell()}>{row.data}</td>
                  <td style={cell()}>{row.nome}</td>
                  <td style={{ ...cell(), fontSize: 14, fontWeight: 800, color: COLORS.orange }}>
                    {row.talhoes.toLocaleString("pt-BR")}
                  </td>
                  <td style={cell()}>
                    {row.processos.map((p) => <Tag key={p} label={p} />)}
                  </td>
                  <td style={cell()}>
                    <div style={{ display: "flex", gap: 8 }}>
                      <ActionButton variant="primary" icon={<GridIcon />}>
                        Ver Resultados
                      </ActionButton>
                      <ActionButton variant="secondary" icon={<FileIcon />}>
                        Ver Tabela Usada
                      </ActionButton>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>

        <Pagination
          page={page}
          totalPages={totalPages}
          totalItems={historico.length}
          itemsPerPage={ITEMS_PER_PAGE}
          onPageChange={(p) => { if (p >= 1 && p <= totalPages) setPage(p); }}
        />
      </div>
    </div>
  );
}

function ActionButton({ variant, icon, children }) {
  const isPrimary = variant === "primary";
  return (
    <button
      style={{
        padding: "6px 12px", borderRadius: 7,
        border: isPrimary ? "none" : `1px solid ${COLORS.gray200}`,
        background: isPrimary ? COLORS.navy : COLORS.white,
        color: isPrimary ? COLORS.white : COLORS.gray800,
        fontSize: 12, fontWeight: 600, cursor: "pointer",
        display: "flex", alignItems: "center", gap: 5,
      }}
    >
      {icon}
      {children}
    </button>
  );
}

function GridIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <rect x="3" y="3" width="18" height="18" rx="2" stroke="white" strokeWidth="2" />
      <line x1="3" y1="9" x2="21" y2="9" stroke="white" strokeWidth="2" />
      <line x1="9" y1="21" x2="9" y2="9" stroke="white" strokeWidth="2" />
    </svg>
  );
}

function FileIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke={COLORS.gray600} strokeWidth="2" />
      <polyline points="14 2 14 8 20 8" stroke={COLORS.gray600} strokeWidth="2" />
    </svg>
  );
}

function cell(extra = {}) {
  return { padding: "13px 14px", fontSize: 13, color: COLORS.gray800, ...extra };
}
