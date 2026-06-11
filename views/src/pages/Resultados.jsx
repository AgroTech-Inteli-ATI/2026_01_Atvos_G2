import { useState, useMemo } from "react";
import { COLORS } from "../constants/theme";
import { RESULTADOS, ITEMS_PER_PAGE } from "../constants/mockData";
import FilterBar from "../components/FilterBar";
import ResultadosTable from "../components/ResultadosTable";
import Pagination from "../components/Pagination";

const EMPTY_FILTERS = { unidade: "", processo: "", insumo: "" };

export default function Resultados() {
  const [pendingFilters, setPendingFilters] = useState(EMPTY_FILTERS);
  const [appliedFilters, setAppliedFilters] = useState(EMPTY_FILTERS);
  const [page, setPage] = useState(1);

  // Só aplica filtros ao clicar em "Buscar"
  const filtered = useMemo(() => {
    return RESULTADOS.filter((row) => {
      if (appliedFilters.unidade  && row.unidade  !== appliedFilters.unidade)  return false;
      if (appliedFilters.processo && row.processo !== appliedFilters.processo) return false;
      if (appliedFilters.insumo   && row.insumo   !== appliedFilters.insumo)   return false;
      return true;
    });
  }, [appliedFilters]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / ITEMS_PER_PAGE));
  const pageRows   = filtered.slice((page - 1) * ITEMS_PER_PAGE, page * ITEMS_PER_PAGE);

  function handleFilterChange(key, value) {
    setPendingFilters((prev) => ({ ...prev, [key]: value }));
  }

  function handleSearch() {
    setAppliedFilters(pendingFilters);
    setPage(1);
  }

  function handleClear() {
    setPendingFilters(EMPTY_FILTERS);
    setAppliedFilters(EMPTY_FILTERS);
    setPage(1);
  }

  function handlePageChange(newPage) {
    if (newPage >= 1 && newPage <= totalPages) setPage(newPage);
  }

  function handleExportCSV() {
    const headers = ["ID_TALHAO", "UNIDADE", "PROCESSO", "ORIENTAÇÃO", "INSUMO", "DOSE KG/HA", "REGRA ACIONADA", "DATA"];
    const rows = filtered.map((r) =>
      [r.id, r.unidade, r.processo, r.orientacao, r.insumo, r.dose, r.regra, r.data].join(";")
    );
    const csv = [headers.join(";"), ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url  = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href     = url;
    link.download = "resultados.csv";
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div style={{ maxWidth: 1280, margin: "0 auto", padding: "32px 24px" }}>
      <FilterBar
        filters={pendingFilters}
        onChange={handleFilterChange}
        onSearch={handleSearch}
        onClear={handleClear}
      />

      <div
        style={{
          background: COLORS.white,
          borderRadius: 12,
          boxShadow: "0 1px 4px rgba(0,0,0,.07)",
          padding: "20px 24px",
        }}
      >
        {/* Export button */}
        <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 16 }}>
          <button
            onClick={handleExportCSV}
            style={{
              padding: "8px 16px",
              borderRadius: 8,
              background: COLORS.navy,
              color: COLORS.white,
              border: "none",
              fontWeight: 700,
              fontSize: 13,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: 6,
            }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" stroke="white" strokeWidth="2" />
              <polyline points="7 10 12 15 17 10" stroke="white" strokeWidth="2" />
              <line x1="12" y1="15" x2="12" y2="3" stroke="white" strokeWidth="2" />
            </svg>
            Exportar CSV
          </button>
        </div>

        <ResultadosTable rows={pageRows} />

        <Pagination
          page={page}
          totalPages={totalPages}
          totalItems={filtered.length}
          itemsPerPage={ITEMS_PER_PAGE}
          onPageChange={handlePageChange}
        />
      </div>
    </div>
  );
}
