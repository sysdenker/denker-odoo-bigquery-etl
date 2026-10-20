import requests
from google.cloud import bigquery

def call_jsonrpc(url, service, method, args):
    """Función auxiliar para estructurar y enviar las peticiones JSON-RPC a Odoo"""
    payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "service": service,
            "method": method,
            "args": args
        },
        "id": 1
    }
    # Asegurar que la URL no termine en diagonal antes de concatenar
    clean_url = url.rstrip('/')
    response = requests.post(f"{clean_url}/jsonrpc", json=payload)

    # Extraer directamente el resultado del JSON devuelto
    return response.json().get("result")

def extraer_e_insertar_partners(odoo_url, odoo_db, odoo_user, odoo_pass, bq_project, bq_dataset):
    print("⏳ Extrayendo datos de Odoo (vía JSON-RPC)...")
    try:
        # 1. Autenticación en Odoo
        uid = call_jsonrpc(odoo_url, "common", "authenticate", [odoo_db, odoo_user, odoo_pass, {}])

        if not uid:
            print(f"❌ Odoo Error: Credenciales incorrectas para la base '{odoo_db}'")
            return

        # 2. Extracción de 5 contactos de prueba
        domain = [[['active', '=', True]]]
        kwargs = {'fields': ['id', 'name', 'email', 'company_type'], 'limit': 5}

        partners = call_jsonrpc(
            odoo_url,
            "object",
            "execute_kw",
            [odoo_db, uid, odoo_pass, 'res.partner', 'search_read', domain, kwargs]
        )

        print(f"✅ Odoo: Se extrajeron {len(partners)} contactos correctamente.")

        # 3. Conexión e inserción en BigQuery
        client = bigquery.Client(project=bq_project)
        table_id = f"{bq_project}.{bq_dataset}.res_partner_estatec"

        schema = [
            bigquery.SchemaField("id", "INTEGER"),
            bigquery.SchemaField("name", "STRING"),
            bigquery.SchemaField("email", "STRING"),
            bigquery.SchemaField("company_type", "STRING"),
        ]

        job_config = bigquery.LoadJobConfig(
            schema=schema,
            write_disposition="WRITE_TRUNCATE",
        )

        print("⏳ Cargando datos a BigQuery...")
        job = client.load_table_from_json(partners, table_id, job_config=job_config)
        job.result()

        print(f"✅ BigQuery: La tabla '{table_id}' se creó/actualizó con {job.output_rows} filas.")

    except Exception as e:
        print(f"❌ Error en el proceso: {e}")
