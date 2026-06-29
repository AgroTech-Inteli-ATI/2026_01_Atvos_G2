import { useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell,
} from "recharts";
import { COLORS } from "../constants/theme";
import AlertIcon from "../components/AlertIcon";
import ImportModal from "../components/ImportModal";
import { usePipeline } from "../context/PipelineContext";

const PIE_COLORS = [COLORS.navy, COLORS.orange];

export default function Dashboard() {
  const [showModal, setShowModal] = useState(false);
  const { metrics, barData, pieData, alertCards } = usePipeline();

  const METRICS_DISPLAY = [
    {
      label: "Total de Talhões",
      value: metrics.total_talhoes?.toLocaleString("pt-BR") ?? "—",
      icon: "🌾",
    },
    {
      label: "Talhões em Alerta",
      value: metrics.talhoes_alerta?.toLocaleString("pt-BR") ?? "—",
      icon: "⚠️",
    },
    {
      label: "% com Dado Ausente",
      value: metrics.pct_dado_ausente != null ? `${metrics.pct_dado_ausente}%` : "—",
      icon: "📊",
    },
    {
      label: "Processos Avaliados",
      value: metrics.processos_avaliados?.toLocaleString("pt-BR") ?? "—",
      icon: "📋",
    },
  ];

  const totalPie = pieData.reduce((s, d) => s + (d.value || 0), 0);

  return (
    <>
      {showModal && (
        <ImportModal
          onClose={() => setShowModal(false)}
          onSuccess={() => setShowModal(false)}
        />
      )}

      <div style={{ maxWidth: 1280, margin: "0 auto", padding: "32px 24px" }}>
        {/* Botão importar */}
        <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 20 }}>
          <button
            onClick={() => setShowModal(true)}
            style={{
              padding: "9px 20px", borderRadius: 8, border: "none",
              background: COLORS.orange, color: COLORS.white,
              fontWeight: 700, fontSize: 13, cursor: "pointer",
              display: "flex", alignItems: "center", gap: 6,
            }}
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" stroke="white" strokeWidth="2" />
              <polyline points="17 8 12 3 7 8" stroke="white" strokeWidth="2" />
              <line x1="12" y1="3" x2="12" y2="15" stroke="white" strokeWidth="2" />
            </svg>
            Importar Lista
          </button>
        </div>

        {/* Cards de métricas */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginBottom: 24 }}>
          {METRICS_DISPLAY.map((m) => (
            <div
              key={m.label}
              style={{
                background: COLORS.white, borderRadius: 12,
                padding: "20px 24px",
                display: "flex", alignItems: "center", justifyContent: "space-between",
                boxShadow: "0 1px 4px rgba(0,0,0,.07)",
              }}
            >
              <div>
                <div style={{ fontSize: 13, color: COLORS.gray600, fontWeight: 500, marginBottom: 6 }}>
                  {m.label}
                </div>
                <div style={{ fontSize: 34, fontWeight: 800, color: COLORS.orange, lineHeight: 1 }}>
                  {m.value}
                </div>
              </div>
              <div style={{
                width: 48, height: 48, background: COLORS.gray100,
                borderRadius: "50%", display: "flex",
                alignItems: "center", justifyContent: "center", fontSize: 22,
              }}>
                {m.icon}
              </div>
            </div>
          ))}
        </div>

        {/* Talhões em alerta */}
        {alertCards.length > 0 && (
          <div style={{ background: COLORS.orange, borderRadius: 14, padding: "22px 24px", marginBottom: 24 }}>
            <div style={{ color: COLORS.white, fontWeight: 800, fontSize: 18, marginBottom: 16 }}>
              Talhões em Alerta
            </div>
            <div style={{
              display: "grid",
              gridTemplateColumns: `repeat(${Math.min(alertCards.length, 4)}, 1fr)`,
              gap: 14,
            }}>
              {alertCards.map((card, i) => (
                <div
                  key={`${card.id}_${i}`}
                  style={{
                    background: "rgba(255,255,255,0.15)", borderRadius: 10,
                    padding: 16, border: "1px solid rgba(255,255,255,0.25)",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                    <div style={{
                      width: 30, height: 30, borderRadius: "50%",
                      border: "1.5px solid rgba(255,255,255,.6)",
                      display: "flex", alignItems: "center",
                      justifyContent: "center", flexShrink: 0,
                    }}>
                      <AlertIcon size={14} color="white" />
                    </div>
                    <span style={{ color: COLORS.white, fontWeight: 700, fontSize: 13 }}>
                      ID: {card.id}
                    </span>
                  </div>
                  <div style={{ color: "rgba(255,255,255,.75)", fontSize: 11, marginBottom: 2 }}>Processo:</div>
                  <div style={{ color: COLORS.white, fontWeight: 700, fontSize: 13, marginBottom: 8 }}>
                    {card.processo}
                  </div>
                  <div style={{ color: "rgba(255,255,255,.75)", fontSize: 11, marginBottom: 2 }}>Orientação:</div>
                  <div style={{ color: COLORS.white, fontSize: 12, lineHeight: 1.5 }}>
                    {card.orientacao}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Gráficos */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
          {/* Bar chart */}
          <div style={{
            background: COLORS.white, borderRadius: 12,
            padding: "22px 24px", boxShadow: "0 1px 4px rgba(0,0,0,.07)",
          }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
              <span style={{ fontWeight: 700, fontSize: 16, color: COLORS.navy }}>
                Orientações por Processo
              </span>
              <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: COLORS.gray600 }}>
                <div style={{ width: 10, height: 10, background: COLORS.navy, borderRadius: 2 }} />
                Total de orientações
              </div>
            </div>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={barData} layout="vertical" margin={{ left: 160, right: 30, top: 0, bottom: 0 }}>
                <CartesianGrid horizontal={false} stroke={COLORS.gray100} />
                <XAxis
                  type="number"
                  tick={{ fontSize: 11, fill: COLORS.gray400 }}
                  axisLine={false} tickLine={false}
                />
                <YAxis
                  type="category" dataKey="name"
                  tick={{ fontSize: 11, fill: COLORS.gray600 }}
                  width={160} axisLine={false} tickLine={false}
                />
                <Tooltip
                  contentStyle={{ borderRadius: 8, border: "none", boxShadow: "0 4px 12px rgba(0,0,0,.1)", fontSize: 12 }}
                  cursor={{ fill: "rgba(26,45,79,.04)" }}
                />
                <Bar
                  dataKey="value" fill={COLORS.navy}
                  radius={[0, 4, 4, 0]}
                  label={{ position: "right", fontSize: 11, fill: COLORS.gray600 }}
                  barSize={16}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Donut chart */}
          <div style={{
            background: COLORS.white, borderRadius: 12,
            padding: "22px 24px", boxShadow: "0 1px 4px rgba(0,0,0,.07)",
          }}>
            <span style={{ fontWeight: 700, fontSize: 16, color: COLORS.navy }}>
              Distribuição por Tipo de Orientação
            </span>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <ResponsiveContainer width="60%" height={220}>
                <PieChart>
                  <Pie
                    data={pieData} dataKey="value"
                    cx="50%" cy="50%"
                    innerRadius={60} outerRadius={90}
                    startAngle={90} endAngle={-270}
                  >
                    {pieData.map((_, i) => (
                      <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <text x="50%" y="50%" textAnchor="middle" dominantBaseline="middle">
                    <tspan x="50%" dy="-8" fontSize="22" fontWeight="800" fill={COLORS.navy}>
                      {totalPie.toLocaleString("pt-BR")}
                    </tspan>
                    <tspan x="50%" dy="22" fontSize="12" fill={COLORS.gray400}>Total</tspan>
                  </text>
                </PieChart>
              </ResponsiveContainer>
              <div style={{ display: "flex", flexDirection: "column", gap: 16, paddingRight: 8 }}>
                {pieData.map((d, i) => (
                  <div key={d.name} style={{ display: "flex", alignItems: "flex-start", gap: 8 }}>
                    <div style={{
                      width: 12, height: 12, borderRadius: 3,
                      background: PIE_COLORS[i % PIE_COLORS.length],
                      flexShrink: 0, marginTop: 2,
                    }} />
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 700, color: COLORS.gray800 }}>{d.name}</div>
                      <div style={{ fontSize: 12, color: COLORS.gray600 }}>
                        {d.value.toLocaleString("pt-BR")} ({d.pct})
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
