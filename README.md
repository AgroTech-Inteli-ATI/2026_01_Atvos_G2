# 2026_01_Atvos_G2 — Motor de Regras Agronômicas

Sistema de recomendações agronômicas para cana-de-açúcar. Processa o inventário de talhões da ATVOS, aplica regras de calagem, gessagem, fosfatagem, erradicação de soqueira e janela de plantio, e exibe os resultados em uma interface web navegável.

---

## Pré-requisitos

| Ferramenta | Versão mínima | Verificar com |
|---|---|---|
| Python | 3.12+ | `python --version` |
| Node.js | 18+ | `node --version` |
| npm | 9+ | `npm --version` |

---

## Instalação

### 1. Dependências Python

```bash
pip install -r requirements.txt
```

### 2. Dependências do frontend

```bash
cd views
npm install
cd ..
```

---

## Rodando o projeto completo

O sistema tem dois processos independentes que precisam estar rodando ao mesmo tempo: a **API Python** e o **frontend React**.

### Terminal 1 — API Python (rodar na raiz do projeto)

```bash
/usr/bin/python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

> A flag `--reload` reinicia a API automaticamente ao salvar qualquer arquivo Python.
>
> **Linux:** use `/usr/bin/python3 -m uvicorn` em vez de `uvicorn` diretamente para garantir que o Python correto (com `fastapi` instalado) seja usado.

Saída esperada:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

### Terminal 2 — Frontend React (rodar dentro de `views/`)

```bash
cd views
npm run dev
```

Saída esperada:
```
  VITE v5.x.x  ready in Xms

  ➜  Local:   http://localhost:5173/
```

### Acessar

Abra **http://localhost:5173** no navegador.

---

## Usando a interface

1. Acesse a aba **Dashboard** ou **Resultados**
2. Clique em **Importar Lista** (botão laranja)
3. Arraste ou selecione um arquivo `.csv` ou `.xlsx`
4. Digite um nome para a importação (ex: `Análise Solo — Junho 2026`)
5. Clique em **Confirmar Importação**

A API processa o arquivo, executa o pipeline Silver → Gold e atualiza automaticamente todas as abas com os resultados reais.

### Formatos de arquivo aceitos

| Formato | Descrição |
|---|---|
| `.xlsx` | Arquivo bruto exportado do sistema ATVOS (colunas `TALHAO`, `UNID_IND`, etc.) |
| `.csv` | CSV no formato silver (já com coluna `id_talhao`) ou exportação CSV do Excel bruto |

O sistema detecta automaticamente o formato e aplica ou não a etapa de limpeza (silver pipeline).

---

## Estrutura do projeto

```
.
├── api/
│   └── main.py              # FastAPI — POST /api/run, GET /api/historico
├── src/
│   ├── processing/
│   │   └── limpeza.py       # Pipeline Silver (limpeza e join com análise de solo)
│   ├── rules/
│   │   ├── calagem.py
│   │   ├── gessagem.py
│   │   ├── fosfatagem.py
│   │   ├── erradicacao.py
│   │   ├── insumos.py
│   │   └── janela_plantio.py
│   └── pipeline_gold.py     # Pipeline Gold (aplica todas as regras)
├── tests/                   # Suite pytest
├── views/                   # Frontend React + Vite
│   └── src/
│       ├── context/
│       │   └── PipelineContext.jsx
│       ├── pages/
│       └── components/
├── DATA/
│   ├── Inventario_atvos.xlsx        # arquivo bruto (não versionado)
│   └── Dados_analise_solo.csv       # análise de solo (não versionado)
├── docs/                    # Documentação Docusaurus
└── requirements.txt
```

---

## Rodando os testes

```bash
pytest tests/ -v
```

---

## Configuração do ambiente (Linux/Unix)

```bash
make setup
```

Copie o arquivo de variáveis de ambiente e preencha com suas credenciais:

```bash
cp .env.example .env
```

---

## Configuração do ambiente (Windows)

### Pré-requisito: Python 3.12

Este projeto requer **Python 3.12**. Versões mais recentes (3.13+) podem não ter pacotes pré-compilados para algumas dependências.

Verifique sua versão atual:
```powershell
python --version
```

Se não estiver na 3.12, baixe o instalador em **python.org** (seção *Downloads → Python 3.12.x*) e instale antes de continuar.

### Passo a passo

1. Crie o ambiente virtual com Python 3.12:
```powershell
py -3.12 -m venv .venv
```

2. Ative o ambiente virtual (no PowerShell):
```powershell
.\.venv\Scripts\Activate.ps1
```

   > **Aviso:** Se você receber um erro sobre scripts desabilitados, abra o PowerShell como Administrador, rode o comando abaixo, confirme com `S` e tente ativar novamente:
   > ```powershell
   > Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   > ```

3. Com o ambiente ativado (você verá um `(.venv)` no início do terminal), instale as dependências:
```powershell
pip install -r requirements.txt
```

4. Rode a API (no diretório raiz do projeto):
```powershell
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

5. Em outro terminal, rode o frontend:
```powershell
cd views
npm install
npm run dev
```
