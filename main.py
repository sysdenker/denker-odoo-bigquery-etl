import os
import xmlrpc.client
from dotenv import load_dotenv
from google.cloud import bigquery

# 1. Cargar la "bóveda" secreta
load_dotenv()
print("👉 REVISIÓN DE BÓVEDA:", os.environ.get("EST_ODOO_URL"))

# 2. Traer las credenciales de Estatec desde el .env
EST_ODOO_URL = os.environ.get("EST_ODOO_URL")
EST_ODOO_DB = os.environ.get("EST_ODOO_DB")
EST_ODOO_USER = os.environ.get("EST_ODOO_USER")
EST_ODOO_PASSWORD = os.environ.get("EST_ODOO_PASSWORD")

# Traer configuraciones de BigQuery
GCP_PROJECT = os.environ.get("GCP_PROJECT", "denker-ia")
BQ_DATASET = os.environ.get("BQ_DATASET", "denker_odoo_master")

def test_bq():
    try:
        client = bigquery.Client(project=GCP_PROJECT)
        dataset = client.get_dataset(f"{GCP_PROJECT}.{BQ_DATASET}")
        print(f"✅ BigQuery: Conectado exitosamente al dataset '{dataset.dataset_id}'")
    except Exception as e:
        print(f"❌ BigQuery Error: {e}")

def test_odoo(url, db, username, password):
    try:
        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        uid = common.authenticate(db, username, password, {})
        if uid:
            print(f"✅ Odoo: Autenticación exitosa en la base '{db}' (UID: {uid})")
        else:
            print(f"❌ Odoo Error: Credenciales incorrectas para '{db}'")
    except Exception as e:
        print(f"❌ Odoo Error de conexión: {e}")

if __name__ == "__main__":
    print("--- INICIANDO PRUEBA DE CONEXIONES ---")
    test_bq()
    test_odoo(EST_ODOO_URL, EST_ODOO_DB, EST_ODOO_USER, EST_ODOO_PASSWORD)
