"""
iDempiere Agent SDK Configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Database Configuration (iDempiere PostgreSQL)
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "database": os.getenv("DB_NAME", "idempiere"),
    "user": os.getenv("DB_USER", "adempiere"),
    "password": os.getenv("DB_PASSWORD", "adempiere"),
}

# Claude API Configuration
CLAUDE_MODEL = "claude-opus-4-6"
CLAUDE_MAX_TOKENS = 4096

# Flask Configuration
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000
FLASK_DEBUG = True

# Entity to Table Mapping
ENTITY_MAPPING = {
    # Sales
    "sales_orders": {
        "table": "c_order",
        "joins": ["c_orderline", "c_bpartner"],
        "key_fields": ["c_order_id", "documentno", "dateordered", "docstatus", "grandtotal"],
        "description": "銷售訂單"
    },
    "invoices": {
        "table": "c_invoice",
        "joins": ["c_invoiceline", "c_bpartner"],
        "key_fields": ["c_invoice_id", "documentno", "dateacct", "docstatus", "grandtotal"],
        "description": "發票"
    },
    "payments": {
        "table": "c_payment",
        "joins": ["c_bpartner"],
        "key_fields": ["c_payment_id", "documentno", "datetrx", "payamt"],
        "description": "收款"
    },

    # Inventory
    "inventory": {
        "table": "m_storage",
        "joins": ["m_product", "m_locator", "m_warehouse"],
        "key_fields": ["m_storage_id", "m_product_id", "qtyonhand", "dateupdate"],
        "description": "庫存"
    },
    "products": {
        "table": "m_product",
        "joins": [],
        "key_fields": ["m_product_id", "value", "name", "description", "uomcode"],
        "description": "產品"
    },

    # Master Data
    "customers": {
        "table": "c_bpartner",
        "where_clause": "isvendor = 'N'",
        "joins": [],
        "key_fields": ["c_bpartner_id", "value", "name", "creditlimit", "totalopencredit"],
        "description": "客戶"
    },
    "suppliers": {
        "table": "c_bpartner",
        "where_clause": "isvendor = 'Y'",
        "joins": [],
        "key_fields": ["c_bpartner_id", "value", "name"],
        "description": "供應商"
    },
}

# SQL Templates for Common Queries
QUERY_TEMPLATES = {
    "sales_by_month": """
        SELECT
            DATE_TRUNC('month', dateordered)::DATE as month,
            COUNT(*) as order_count,
            SUM(grandtotal) as total_sales,
            AVG(grandtotal) as avg_order_value
        FROM c_order
        WHERE docstatus IN ('CO', 'CL')
        {where_clause}
        GROUP BY DATE_TRUNC('month', dateordered)
        ORDER BY month DESC
    """,

    "sales_by_customer": """
        SELECT
            bp.name as customer_name,
            COUNT(co.c_order_id) as order_count,
            SUM(co.grandtotal) as total_sales,
            AVG(co.grandtotal) as avg_order_value
        FROM c_order co
        JOIN c_bpartner bp ON co.c_bpartner_id = bp.c_bpartner_id
        WHERE co.docstatus IN ('CO', 'CL')
        {where_clause}
        GROUP BY bp.c_bpartner_id, bp.name
        ORDER BY total_sales DESC
    """,

    "sales_by_product": """
        SELECT
            mp.name as product_name,
            mp.value as product_code,
            SUM(col.qtyordered) as total_qty,
            SUM(col.linenetamt) as total_sales
        FROM c_orderline col
        JOIN m_product mp ON col.m_product_id = mp.m_product_id
        JOIN c_order co ON col.c_order_id = co.c_order_id
        WHERE co.docstatus IN ('CO', 'CL')
        {where_clause}
        GROUP BY mp.m_product_id, mp.name, mp.value
        ORDER BY total_sales DESC
    """,

    "inventory_status": """
        SELECT
            mp.name as product_name,
            mp.value as product_code,
            SUM(ms.qtyonhand) as qty_on_hand,
            SUM(ms.qtyonhand * mp.standardcostamt) as inventory_value,
            MAX(ms.dateupdate) as last_update
        FROM m_storage ms
        JOIN m_product mp ON ms.m_product_id = mp.m_product_id
        {where_clause}
        GROUP BY mp.m_product_id, mp.name, mp.value
        ORDER BY inventory_value DESC
    """,

    "ar_aging": """
        SELECT
            bp.name as customer_name,
            ci.documentno as invoice_no,
            ci.dateacct,
            ci.grandtotal as amount,
            ci.grandtotal - COALESCE(sum_paid.paid_amount, 0) as outstanding,
            (NOW()::DATE - ci.dateacct) as days_overdue
        FROM c_invoice ci
        JOIN c_bpartner bp ON ci.c_bpartner_id = bp.c_bpartner_id
        LEFT JOIN (
            SELECT c_invoice_id, SUM(payamt) as paid_amount
            FROM c_payment
            GROUP BY c_invoice_id
        ) sum_paid ON ci.c_invoice_id = sum_paid.c_invoice_id
        WHERE ci.docstatus IN ('CO', 'CL')
        {where_clause}
        ORDER BY days_overdue DESC
    """,
}

print("✅ Config loaded successfully")
