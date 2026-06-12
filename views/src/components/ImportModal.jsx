import { useRef, useState } from "react";
import { COLORS } from "../constants/theme";
import { usePipeline } from "../context/PipelineContext";

export default function ImportModal({ onClose, onSuccess }) {
  const { runPipeline, isLoading } = usePipeline();
  const [dragging, setDragging] = useState(false);
  const [file, setFile] = useState(null);
  const [listName, setListName] = useState("");
  const [error, setError] = useState(null);
  const inputRef = useRef(null);

  function handleFile(f) {
    if (!f) return;
    const ext = f.name.split(".").pop().toLowerCase();
    if (!["csv", "xlsx", "xls"].includes(ext)) {
      setError("Formato inválido. Use .csv ou .xlsx");
      return;
    }
    setError(null);
    setFile(f);
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragging(false);
    handleFile(e.dataTransfer.files[0]);
  }

  async function handleConfirm() {
    if (!file || !listName.trim() || isLoading) return;
    const result = await runPipeline(file, listName.trim());
    if (result.success) {
      onSuccess?.();
      onClose();
    } else {
      setError(result.error || "Erro ao processar o arquivo. Verifique se a API está rodando.");
    }
  }

  const canConfirm = !!file && !!listName.trim() && !isLoading;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      style={{
        position: "fixed", inset: 0,
        background: "rgba(0,0,0,.45)",
        display: "flex", alignItems: "center", justifyContent: "center",
        zIndex: 1000,
      }}
      onClick={(e) => e.target === e.currentTarget && !isLoading && onClose()}
    >
      <div
        style={{
          background: COLORS.white,
          borderRadius: 14,
          width: 580,
          boxShadow: "0 20px 60px rgba(0,0,0,.25)",
          overflow: "hidden",
          animation: "fadeIn .2s ease",
        }}
      >
        {/* Header */}
        <div
          style={{
            background: COLORS.orange,
            padding: "16px 24px",
            display: "flex", alignItems: "center", justifyContent: "space-between",
          }}
        >
          <span id="modal-title" style={{ color: COLORS.white, fontWeight: 800, fontSize: 17 }}>
            Importar Lista de Talhões
          </span>
          <button
            onClick={onClose}
            disabled={isLoading}
            aria-label="Fechar modal"
            style={{
              background: "none", border: "none",
              color: COLORS.white, fontSize: 22,
              cursor: isLoading ? "not-allowed" : "pointer", lineHeight: 1,
            }}
          >
            ×
          </button>
        </div>

        {/* Body */}
        <div style={{ padding: "28px 28px 24px" }}>
          {/* Drop zone */}
          <div
            onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
            onClick={() => !isLoading && inputRef.current?.click()}
            style={{
              border: `2px dashed ${dragging ? COLORS.orange : "#d1d5db"}`,
              borderRadius: 10,
              padding: "40px 20px",
              display: "flex", flexDirection: "column", alignItems: "center",
              gap: 10,
              cursor: isLoading ? "not-allowed" : "pointer",
              transition: "border-color .2s",
              background: dragging ? COLORS.orangePale : COLORS.gray50,
              marginBottom: 20,
            }}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".csv,.xlsx,.xls"
              style={{ display: "none" }}
              onChange={(e) => handleFile(e.target.files[0])}
            />
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" stroke={COLORS.gray400} strokeWidth="1.8" />
              <polyline points="17 8 12 3 7 8" stroke={COLORS.gray400} strokeWidth="1.8" />
              <line x1="12" y1="3" x2="12" y2="15" stroke={COLORS.gray400} strokeWidth="1.8" />
            </svg>
            <span style={{ color: COLORS.gray600, fontSize: 14 }}>
              {file ? `✓ ${file.name}` : "Arraste o arquivo aqui ou clique para selecionar"}
            </span>
            {!file && (
              <span style={{ color: COLORS.gray400, fontSize: 12 }}>.csv / .xlsx</span>
            )}
          </div>

          {/* Nome da lista */}
          <label
            htmlFor="list-name"
            style={{ display: "block", fontSize: 13, fontWeight: 600, color: COLORS.gray800, marginBottom: 6 }}
          >
            Nome da lista
          </label>
          <input
            id="list-name"
            value={listName}
            disabled={isLoading}
            onChange={(e) => setListName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleConfirm()}
            placeholder="Ex: Análise Solo — Junho 2026"
            style={{
              width: "100%", padding: "11px 14px",
              borderRadius: 8, border: `1px solid ${COLORS.gray200}`,
              fontSize: 14, color: COLORS.gray800, outline: "none",
              boxSizing: "border-box", marginBottom: error ? 12 : 24,
            }}
          />

          {/* Erro */}
          {error && (
            <div style={{
              color: "#dc2626", fontSize: 13, marginBottom: 16,
              padding: "8px 12px", background: "#fef2f2",
              borderRadius: 6, border: "1px solid #fecaca",
            }}>
              {error}
            </div>
          )}

          {/* Loading */}
          {isLoading && (
            <div style={{
              marginBottom: 16, fontSize: 13, color: COLORS.gray600,
              display: "flex", alignItems: "center", gap: 8,
            }}>
              <div style={{
                width: 16, height: 16, borderRadius: "50%",
                border: `2px solid ${COLORS.orange}`,
                borderTopColor: "transparent",
                animation: "spin .8s linear infinite",
              }} />
              Processando pipeline... aguarde.
            </div>
          )}

          {/* Ações */}
          <div style={{ display: "flex", gap: 12, justifyContent: "flex-end" }}>
            <button
              onClick={onClose}
              disabled={isLoading}
              style={{
                padding: "10px 24px", borderRadius: 8,
                border: `1.5px solid ${COLORS.navy}`,
                background: COLORS.white, color: COLORS.navy,
                fontWeight: 700, fontSize: 14,
                cursor: isLoading ? "not-allowed" : "pointer",
                opacity: isLoading ? 0.5 : 1,
              }}
            >
              Cancelar
            </button>
            <button
              onClick={handleConfirm}
              disabled={!canConfirm}
              style={{
                padding: "10px 24px", borderRadius: 8, border: "none",
                background: COLORS.navy, color: COLORS.white,
                fontWeight: 700, fontSize: 14,
                cursor: canConfirm ? "pointer" : "not-allowed",
                opacity: canConfirm ? 1 : 0.5,
              }}
            >
              {isLoading ? "Processando..." : "Confirmar Importação"}
            </button>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes fadeIn { from { opacity:0; transform:scale(.96) } to { opacity:1; transform:scale(1) } }
        @keyframes spin { to { transform: rotate(360deg) } }
      `}</style>
    </div>
  );
}
