import requests
from google.cloud import bigquery

def call_jsonrpc(url, service, method, args):
    """Función auxiliar para enviar peticiones JSON-RPC a Odoo"""
    payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {"service": service, "method": method, "args": args},
        "id": 1
    }
    clean_url = url.rstrip('/')
    response = requests.post(f"{clean_url}/jsonrpc", json=payload)

    # --- ESCUDO CONTRA ERRORES HTML DE TIEMPO DE ESPERA ---
    try:
        respuesta_json = response.json()
    except Exception:
        print(f"\n🚨 ERROR DEL SERVIDOR (El servidor colapsó o tardó demasiado). Código HTTP: {response.status_code}")
        print(f"Respuesta del servidor: {response.text[:200]}...") # Imprime un fragmento del error
        return []

    if "error" in respuesta_json:
        print("\n🚨 ODOO RECHAZÓ LA PETICIÓN. DETALLE DEL ERROR:")
        print(respuesta_json["error"].get("data", {}).get("message", respuesta_json["error"]))
        return []

    return respuesta_json.get("result", [])

def extraer_e_insertar_ventas(odoo_url, odoo_db, odoo_user, odoo_pass, bq_project, bq_dataset):
    print("⏳ Extrayendo ventas de la vista materializada de Odoo (ESTATEC)...")
    try:
        # 1. Autenticación
        uid = call_jsonrpc(odoo_url, "common", "authenticate", [odoo_db, odoo_user, odoo_pass, {}])
        if not uid:
            print(f"❌ Odoo Error: Credenciales incorrectas para '{odoo_db}'")
            return

        # 2. Filtros según regla RC-2: Solo facturas y NC de clientes, en estado 'posted'
        domain = [
            ['x_move_type', 'in', ['out_invoice', 'out_refund']],
            ['x_state', '=', 'posted']
        ]

        # Campos exactos de la Ficha 3.4 del documento de Gobernanza
        campos_odoo = [
            'x_move_id', 'x_name', 'x_invoice_date', 'x_company_id',
            'x_commercial_partner_id', 'x_country_id', 'x_team_id',
            'x_invoice_user_id', 'x_move_type', 'x_account_id',
            'x_journal_id', 'x_fiscal_position_id', 'x_dnk_family_id',
            'x_dnk_subfamily_id', 'x_product_id', 'x_default_code',
            'x_quantity', 'x_currency_id', 'x_dnk_usd_subtotal',
            'x_price_subtotal', 'x_dnk_invoice_origin',
            'x_dnk_sale_city_id', 'x_medium_id', 'x_state'
        ]

        kwargs = {
            'fields': campos_odoo,
            'limit': 50
        }

        # Extracción apuntando a tu vista materializada
        ventas_crudas = call_jsonrpc(
            odoo_url, "object", "execute_kw",
            [odoo_db, uid, odoo_pass, 'x_bi_sql_view.mv_account_invoice_report', 'search_read', [domain], kwargs]
        )
        print(f"✅ Odoo: Se extrajeron {len(ventas_crudas)} renglones de venta.")

        # 3. Transformación: Regla RC-1 (Inyectar base_odoo y aplanar datos)
        ventas_limpias = []
        for v in ventas_crudas:
            # Función auxiliar para sacar el ID o Nombre de los campos relacionales (ej. [1, "Antiestatica"])
            def get_val(field_data, index=0):
                if isinstance(field_data, list) and len(field_data) > index:
                    return field_data[index]
                return field_data if not isinstance(field_data, list) else None

            fila = {
                "id_factura": get_val(v.get('x_move_id')),
                "folio": v.get('x_name'),
                "fecha_factura": v.get('x_invoice_date'),
                "razon_social_id": get_val(v.get('x_company_id')),
                "razon_social": get_val(v.get('x_company_id'), 1),
                "cliente_id": get_val(v.get('x_commercial_partner_id')),
                "cliente": get_val(v.get('x_commercial_partner_id'), 1),
                "tipo_documento": v.get('x_move_type'),
                "cuenta_contable_id": get_val(v.get('x_account_id')),
                "cantidad": v.get('x_quantity'),
                "subtotal_usd": v.get('x_dnk_usd_subtotal'),
                "subtotal_moneda_cia": v.get('x_price_subtotal'),
                "estatus_documento": v.get('x_state'),
                "base_odoo": "ESTATEC" # <--- Regla RC-1 Inyectada
            }
            ventas_limpias.append(fila)

        # 4. Conexión a BigQuery
        client = bigquery.Client(project=bq_project)
        table_id = f"{bq_project}.{bq_dataset}.dnk_ventas_general"

        # Esquema de la tabla maestra
        schema = [
            bigquery.SchemaField("id_factura", "INTEGER"),
            bigquery.SchemaField("folio", "STRING"),
            bigquery.SchemaField("fecha_factura", "DATE"),
            bigquery.SchemaField("razon_social_id", "INTEGER"),
            bigquery.SchemaField("razon_social", "STRING"),
            bigquery.SchemaField("cliente_id", "INTEGER"),
            bigquery.SchemaField("cliente", "STRING"),
            bigquery.SchemaField("tipo_documento", "STRING"),
            bigquery.SchemaField("cuenta_contable_id", "INTEGER"),
            bigquery.SchemaField("cantidad", "FLOAT"),
            bigquery.SchemaField("subtotal_usd", "FLOAT"),
            bigquery.SchemaField("subtotal_moneda_cia", "FLOAT"),
            bigquery.SchemaField("estatus_documento", "STRING"),
            bigquery.SchemaField("base_odoo", "STRING"),
        ]

        # WRITE_APPEND para que cuando conectemos Denker, se sumen abajo
        job_config = bigquery.LoadJobConfig(
            schema=schema,
            write_disposition="WRITE_TRUNCATE", # Cambiaremos a APPEND cuando juntemos ambas
        )

        print("⏳ Cargando datos a BigQuery...")
        job = client.load_table_from_json(ventas_limpias, table_id, job_config=job_config)
        job.result()

        print(f"✅ BigQuery: La tabla '{table_id}' está lista con {job.output_rows} filas.")

    except Exception as e:
        print(f"❌ Error en el proceso: {e}")
