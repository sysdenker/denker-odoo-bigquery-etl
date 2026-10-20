import os

# Credenciales de Odoo Estatec
EST_ODOO_URL = os.environ.get("EST_ODOO_URL", "https://estatec.odoo.com")
EST_ODOO_DB = os.environ.get("EST_ODOO_DB", "estatec-main-27045210")
EST_ODOO_USER = os.environ.get("EST_ODOO_USER", "sofia@grupodenker.com")
EST_ODOO_PASSWORD = os.environ.get("EST_ODOO_PASSWORD", "2f9ca6efa105638a90cf1ab2d3ce90d7e977c774")

# Credenciales de Odoo Denker
EXT_ODOO_URL = os.environ.get("EXT_ODOO_URL", "https://grupodenker.odoo.com")
EXT_ODOO_DB = os.environ.get("EXT_ODOO_DB", "grupodenker-master-113629")
EXT_ODOO_USER = os.environ.get("EXT_ODOO_USER", "sofia@grupodenker.com")
EXT_ODOO_PASSWORD = os.environ.get("EXT_ODOO_PASSWORD", "0e842f3d232cd360bf612389809ed6186846c554")

# Configuración de Google Cloud
GCP_PROJECT = os.environ.get("GCP_PROJECT", "denker-ia")
BQ_DATASET = os.environ.get("BQ_DATASET", "denker_odoo_master")
