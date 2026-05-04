# 2026_01_Atvos_G2

## Configuração do ambiente

1. Instale as dependências Python:
   ```bash
   pip install -r requirements.txt
   ```

2. Copie o arquivo de exemplo e preencha com suas credenciais:
   ```bash
   cp .env.example .env
   ```

3. Teste a conexão com GCP:
   ```bash
   python src/ingestion/test_connection.py
   ```