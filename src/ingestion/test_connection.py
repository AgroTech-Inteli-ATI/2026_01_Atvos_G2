import os
import sys
from dotenv import load_dotenv

load_dotenv()

required_vars = ["GCP_PROJECT_ID", "GCP_BUCKET_NAME", "GOOGLE_APPLICATION_CREDENTIALS"]
missing = [v for v in required_vars if not os.getenv(v)]
if missing:
    print(f"[ERRO] Variáveis de ambiente ausentes: {', '.join(missing)}")
    print("Copie .env.example para .env e preencha os valores.")
    sys.exit(1)

project_id = os.getenv("GCP_PROJECT_ID")
bucket_name = os.getenv("GCP_BUCKET_NAME")


def test_bigquery():
    from google.cloud import bigquery

    client = bigquery.Client(project=project_id)
    datasets = list(client.list_datasets())
    print(f"[OK] BigQuery conectado ao projeto '{project_id}' — {len(datasets)} dataset(s) encontrado(s).")


def test_storage():
    from google.cloud import storage

    client = storage.Client(project=project_id)
    bucket = client.bucket(bucket_name)
    exists = bucket.exists()
    if not exists:
        raise RuntimeError(f"Bucket '{bucket_name}' não encontrado no projeto '{project_id}'.")
    print(f"[OK] Cloud Storage conectado — bucket '{bucket_name}' acessível.")


if __name__ == "__main__":
    try:
        test_bigquery()
        test_storage()
        print("\nAmbiente configurado corretamente.")
    except Exception as e:
        print(f"\n[ERRO] {e}")
        sys.exit(1)
