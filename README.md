# 2026_01_Atvos_G2

## Como executar a pipeline

Com o ambiente configurado e os arquivos de dados na pasta `DATA/`, rode:

```bash
python src/pipeline_gold.py
```

Isso executa as duas fases em sequência:
1. **Silver** — limpeza do inventário e join com análise de solo
2. **Gold** — motor de regras agronômicas (calagem, gessagem, fosfatagem, erradicação)

Os arquivos de saída são gerados em `DATA/gold/orientacoes_YYYY-MM-DD.[parquet|csv]`.

**Arquivos necessários em `DATA/`:**
- `Inventario_atvos.xlsx`
- `Dados_analise_solo.csv`

---

## Caminho 1 - Sistemas Unix → Configuração do ambiente

1. Configure o ambiente:
   ```bash
   make setup
   ```

2. Copie o arquivo de variáveis de ambiente e preencha com suas credenciais:
   ```bash
   cp .env.example .env
   ```

3. Coloque os arquivos de dados na pasta `DATA/`.


## Caminho 2 — Sistemas Windows → Configuração do ambiente

### Pré-requisito: Python 3.12

Este projeto requer **Python 3.12**. Versões mais recentes (3.13+) não possuem pacotes pré-compilados para algumas dependências (como o `pandas`), causando erros de instalação.

Verifique sua versão atual:
```powershell
python --version
```

Se não estiver na 3.12, baixe o instalador em **python.org** (seção *Downloads → Python 3.12.x*) e instale antes de continuar.

---

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

   > **Erro durante a instalação do pandas?** Confirme que o ambiente foi criado com Python 3.12 (passo 1). Se o venv já existia com outra versão, delete-o e recrie:
   > ```powershell
   > deactivate
   > Remove-Item -Recurse -Force .venv
   > py -3.12 -m venv .venv
   > .\.venv\Scripts\Activate.ps1
   > pip install -r requirements.txt
   > ```

4. Crie a pasta `data` (se ainda não existir) e adicione os arquivos CSV dentro dela:
```powershell
   mkdir data -Force
```