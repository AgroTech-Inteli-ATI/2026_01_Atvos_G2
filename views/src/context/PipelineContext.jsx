import { createContext, useCallback, useContext, useEffect, useState } from "react";
import {
  RESULTADOS, BAR_DATA, PIE_DATA, ALERT_CARDS, HISTORICO,
} from "../constants/mockData";

const MOCK_METRICS = {
  total_talhoes:       1248,
  talhoes_alerta:      32,
  pct_dado_ausente:    14.6,
  processos_avaliados: 18,
};

const PipelineContext = createContext(null);

export function PipelineProvider({ children }) {
  const [state, setState] = useState({
    resultados:  RESULTADOS,
    metrics:     MOCK_METRICS,
    barData:     BAR_DATA,
    pieData:     PIE_DATA,
    alertCards:  ALERT_CARDS,
    historico:   HISTORICO,
    isLoading:   false,
    hasRealData: false,
    error:       null,
  });

  // Carrega histórico real da API ao iniciar (silencioso se API offline)
  useEffect(() => {
    fetch("/api/historico")
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data?.historico?.length) {
          setState((prev) => ({ ...prev, historico: data.historico }));
        }
      })
      .catch(() => {});
  }, []);

  const runPipeline = useCallback(async (file, nome) => {
    setState((prev) => ({ ...prev, isLoading: true, error: null }));
    try {
      const form = new FormData();
      form.append("file", file);
      form.append("nome", nome);

      const res = await fetch("/api/run", { method: "POST", body: form });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Erro desconhecido" }));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      const data = await res.json();

      setState((prev) => ({
        resultados:  data.resultados,
        metrics:     data.metrics,
        barData:     data.bar_data,
        pieData:     data.pie_data,
        alertCards:  data.alert_cards,
        historico:   [data.historico_entry, ...prev.historico],
        isLoading:   false,
        hasRealData: true,
        error:       null,
      }));

      return { success: true };
    } catch (err) {
      setState((prev) => ({ ...prev, isLoading: false, error: err.message }));
      return { success: false, error: err.message };
    }
  }, []);

  return (
    <PipelineContext.Provider value={{ ...state, runPipeline }}>
      {children}
    </PipelineContext.Provider>
  );
}

export function usePipeline() {
  const ctx = useContext(PipelineContext);
  if (!ctx) throw new Error("usePipeline deve ser usado dentro de PipelineProvider");
  return ctx;
}
