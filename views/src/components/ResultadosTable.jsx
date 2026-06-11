import { useState } from "react";
import { COLORS } from "../constants/theme";
import AlertIcon from "./AlertIcon";

const COLUMNS = [
  { key: "id",         label: "ID_TALHAO"      },
  { key: "unidade",    label: "UNIDADE"         },
  { key: "processo",   label: "PROCESSO"        },
  { key: "orientacao", label: "ORIENTAÇÃO"      },
  { key: "dose",       label: "VALOR CALC."     },
  { key: "regra",      label: "REGRA ACIONADA"  },
  { key: "data",       label: "DATA"            },
];

export default function ResultadosTable({ rows }) {
  const [hoveredRow, setHoveredRow] = useState(null);

  if (rows.length === 0) {
    return (
      <div
        style={{
          padding: "48px 0",
          textAlign: "center",
          color: COLORS.gray400,
          fontSize: 14,
        }}
      >
        Nenhum resultado encontrado para os filtros selecionados.
      </div>
    );
  }

  return (
    <table style={{ width: "100%", borderCollapse: "collapse" }}>
      <thead>
        <tr style={{ background: COLORS.orangeLight }}>
          {COLUMNS.map((col) => (
            <th
              key={col.key}
              style={{
                padding: "10px 12px",
                textAlign: "left",
                fontSize: 11,
                fontWeight: 700,
                color: COLORS.orange,
                letterSpacing: ".06em",
              }}
            >
              {col.label}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, i) => {
          const isHovered = hoveredRow === row.id;
          const bg = row.alert
            ? COLORS.rowHighlight
            : isHovered
            ? COLORS.gray50
            : i % 2 === 0
            ? COLORS.white
            : COLORS.gray50;

          return (
            <tr
              key={row.id}
              onMouseEnter={() => setHoveredRow(row.id)}
              onMouseLeave={() => setHoveredRow(null)}
              style={{
                background: bg,
                borderBottom: `1px solid ${COLORS.gray100}`,
                transition: "background .15s",
              }}
            >
              <td style={cell({ fontWeight: 600, color: COLORS.navy })}>{row.id}</td>
              <td style={cell()}>{row.unidade}</td>
              <td style={cell()}>{row.processo}</td>
              <td style={cell()}>
                <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  {row.alert && <AlertIcon size={14} color={COLORS.orange} />}
                  {row.orientacao}
                </div>
              </td>
              <td style={cell()}>{row.dose}</td>
              <td style={cell()}>{row.regra}</td>
              <td style={cell({ color: COLORS.gray600 })}>{row.data}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

function cell(extra = {}) {
  return {
    padding: "11px 12px",
    fontSize: 13,
    color: COLORS.gray800,
    ...extra,
  };
}
