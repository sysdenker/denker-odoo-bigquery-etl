import os
from dotenv import load_dotenv

# Importamos la nueva función con el nombre correcto
from extractors.dnk_ventas_general import extraer_e_insertar_ventas

load_dotenv()

EST_ODOO_URL = os.environ.get("EST_ODOO_URL")
EST_ODOO_DB = os.environ.get("EST_ODOO_DB")
EST_ODOO_USER = os.environ.get("EST_ODOO_USER")
EST_ODOO_PASSWORD = os.environ.get("EST_ODOO_PASSWORD")

GCP_PROJECT = os.environ.get("GCP_PROJECT")
BQ_DATASET = os.environ.get("BQ_DATASET")

if __name__ == "__main__":
    print("--- INICIANDO EXTRACCIÓN OFICIAL DE VENTAS ---")
    # Ejecutamos la función con el nombre correcto
    extraer_e_insertar_ventas(
        EST_ODOO_URL, EST_ODOO_DB, EST_ODOO_USER, EST_ODOO_PASSWORD,
        GCP_PROJECT, BQ_DATASET
    )
