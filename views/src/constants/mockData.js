import rawCsv2205 from '../../../DATA/gold/orientacoes_2026-05-22.csv?raw';
import rawCsv1205 from '../../../DATA/gold/orientacoes_2026-05-12.csv?raw';

// ── Parser CSV (lida com campos entre aspas que contêm vírgulas) ─────────────
function parseCsvLine(line) {
  const result = [];
  let current = '';
  let inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (ch === '"') {
      inQuotes = !inQuotes;
    } else if (ch === ',' && !inQuotes) {
      result.push(current);
      current = '';
    } else {
      current += ch;
    }
  }
  result.push(current);
  return result;
}

function parseCsv(raw) {
  const lines = raw.trim().split('\n');
  const headers = parseCsvLine(lines[0]);
  return lines.slice(1).map(line => {
    const vals = parseCsvLine(line);
    return Object.fromEntries(headers.map((h, i) => [h, (vals[i] ?? '').trim()]));
  });
}

// ── Parse dos arquivos gold ──────────────────────────────────────────────────
const raw2205 = parseCsv(rawCsv2205);
const raw1205 = parseCsv(rawCsv1205);

// ── Lógica de alerta: regras que exigem ação real ────────────────────────────
function isAlert(regra) {
  return (
    !regra.startsWith('sem_necessidade') &&
    !regra.startsWith('nao_aplicavel') &&
    !regra.startsWith('janela')
  );
}

// ── Mapeamento gold → shape do frontend ─────────────────────────────────────
function mapRow(r) {
  return {
    id:         r.id_talhao,
    unidade:    r.unidade,
    processo:   r.processo,
    orientacao: r.orientacao,
    dose:       r.valor_calculado || '—',
    regra:      r.regra_acionada,
    data:       r.data_geracao,
    alert:      isAlert(r.regra_acionada),
  };
}

// ── Exports principais ───────────────────────────────────────────────────────
export const RESULTADOS = raw2205.map(mapRow);

export const UNIDADES  = [...new Set(raw2205.map(r => r.unidade))].sort();
export const PROCESSOS = [...new Set(raw2205.map(r => r.processo))].sort();

// BAR_DATA: total de orientações por processo
const processoCounts = raw2205.reduce((acc, r) => {
  acc[r.processo] = (acc[r.processo] || 0) + 1;
  return acc;
}, {});
export const BAR_DATA = Object.entries(processoCounts)
  .map(([name, value]) => ({ name, value }))
  .sort((a, b) => b.value - a.value);

// PIE_DATA: corretiva (com alerta) vs preventiva (sem alerta)
const alertCount = RESULTADOS.filter(r => r.alert).length;
const total      = RESULTADOS.length;
const prevCount  = total - alertCount;
export const PIE_DATA = [
  {
    name:  'Preventiva',
    value: prevCount,
    pct:   `${((prevCount / total) * 100).toFixed(1).replace('.', ',')}%`,
  },
  {
    name:  'Corretiva',
    value: alertCount,
    pct:   `${((alertCount / total) * 100).toFixed(1).replace('.', ',')}%`,
  },
];

// ALERT_CARDS: primeiros 4 talhões com alerta
export const ALERT_CARDS = RESULTADOS
  .filter(r => r.alert)
  .slice(0, 4)
  .map(r => ({ id: r.id, processo: r.processo, orientacao: r.orientacao }));

// HISTORICO: derivado dos dois arquivos gold disponíveis
function makeHistoricoEntry(rows) {
  const date      = rows[0]?.data_geracao ?? '';
  const talhoes   = new Set(rows.map(r => r.id_talhao)).size;
  const processos = [...new Set(rows.map(r => r.processo))];
  return { data: date, nome: `Análise Gold — ${date}`, talhoes, processos };
}
export const HISTORICO = [
  makeHistoricoEntry(raw2205),
  makeHistoricoEntry(raw1205),
];

export const ITEMS_PER_PAGE = 10;
