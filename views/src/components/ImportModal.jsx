import { useState } from "react";
import { COLORS } from "../constants/theme";

export default function ImportModal({ onClose, onConfirm }) {
  const [dragging, setDragging] = useState(false);
  const [fileName, setFileName] = useState(null);
  const [listName, setListName] = useState("");

  function handleFile(file) {
    if (file) setFileName(file.name);
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragging(false);
    handleFile(e.dataTransfer.files[0]);
  }

  function handleClick() {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".csv,.parquet";
    input.onchange = (e) => handleFile(e.target.files[0]);
    input.click();
  }

  function handleConfirm() {
    if (!fileName || !listName.trim()) return;
    onConfirm?.({ fileName, listName });
    onClose();
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,.45)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
      }}
      onClick={(e) => e.target === e.currentTarget && onClose()}
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
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <span id="modal-title" style={{ color: COLORS.white, fontWeight: 800, fontSize: 17 }}>
            Importar Lista de Talhões
          </span>
          <button
            onClick={onClose}
            aria-label="Fechar modal"
            style={{ background: "none", border: "none", color: COLORS.white, fontSize: 22, cursor: "pointer", lineHeight: 1 }}
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
            onClick={handleClick}
            style={{
              border: `2px dashed ${dragging ? COLORS.orange : "#d1d5db"}`,
              borderRadius: 10,
              padding: "40px 20px",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 10,
              cursor: "pointer",
              transition: "border-color .2s",
              background: dragging ? COLORS.orangePale : COLORS.gray50,
              marginBottom: 20,
            }}
          >
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" stroke={COLORS.gray400} strokeWidth="1.8" />
              <polyline points="17 8 12 3 7 8" stroke={COLORS.gray400} strokeWidth="1.8" />
              <line x1="12" y1="3" x2="12" y2="15" stroke={COLORS.gray400} strokeWidth="1.8" />
            </svg>
            <span style={{ color: COLORS.gray600, fontSize: 14 }}>
              {fileName ? `✓ ${fileName}` : "Arraste o arquivo aqui ou clique para selecionar"}
            </span>
            {!fileName && (
              <span style={{ color: COLORS.gray400, fontSize: 12 }}>.csv / .parquet</span>
            )}
          </div>

          {/* Name field */}
          <label
            htmlFor="list-name"
            style={{ display: "block", fontSize: 13, fontWeight: 600, color: COLORS.gray800, marginBottom: 6 }}
          >
            Nome da lista
          </label>
          <input
            id="list-name"
            value={listName}
            onChange={(e) => setListName(e.target.value)}
            placeholder="Ex: Análise Solo — Maio 2026"
            style={{
              width: "100%",
              padding: "11px 14px",
              borderRadius: 8,
              border: `1px solid ${COLORS.gray200}`,
              fontSize: 14,
              color: COLORS.gray800,
              outline: "none",
              boxSizing: "border-box",
              marginBottom: 24,
            }}
          />

          {/* Actions */}
          <div style={{ display: "flex", gap: 12, justifyContent: "flex-end" }}>
            <button
              onClick={onClose}
              style={{
                padding: "10px 24px",
                borderRadius: 8,
                border: `1.5px solid ${COLORS.navy}`,
                background: COLORS.white,
                color: COLORS.navy,
                fontWeight: 700,
                fontSize: 14,
                cursor: "pointer",
              }}
            >
              Cancelar
            </button>
            <button
              onClick={handleConfirm}
              disabled={!fileName || !listName.trim()}
              style={{
                padding: "10px 24px",
                borderRadius: 8,
                border: "none",
                background: COLORS.navy,
                color: COLORS.white,
                fontWeight: 700,
                fontSize: 14,
                cursor: !fileName || !listName.trim() ? "not-allowed" : "pointer",
                opacity: !fileName || !listName.trim() ? 0.5 : 1,
              }}
            >
              Confirmar Importação
            </button>
          </div>
        </div>
      </div>

      <style>{`@keyframes fadeIn { from { opacity:0; transform:scale(.96) } to { opacity:1; transform:scale(1) } }`}</style>
    </div>
  );
}
