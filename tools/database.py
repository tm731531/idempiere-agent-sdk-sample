"""
Tool #1: Database Query Tool
智能查詢 iDempiere 資料庫的工具
"""
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from config import DB_CONFIG, ENTITY_MAPPING, QUERY_TEMPLATES


class DatabaseTool:
    """
    通用資料庫查詢工具

    特性：
    - 自動選擇正確的表和 JOIN
    - 支持過濾、排序、分組、聚合
    - 自動格式化結果
    """

    def __init__(self):
        self.conn = None

    def connect(self):
        """連接到資料庫"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            print("✅ Database connected")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            raise

    def close(self):
        """關閉連接"""
        if self.conn:
            self.conn.close()

    def query_sales_orders(self, filters=None, limit=100):
        """查詢銷售訂單"""
        query = """
            SELECT
                co.c_order_id,
                co.documentno,
                co.dateordered,
                co.docstatus,
                bp.name as customer_name,
                co.grandtotal,
                COUNT(col.c_orderline_id) as line_count
            FROM adempiere.c_order co
            LEFT JOIN adempiere.c_bpartner bp ON co.c_bpartner_id = bp.c_bpartner_id
            LEFT JOIN adempiere.c_orderline col ON co.c_order_id = col.c_order_id
            WHERE 1=1
        """

        params = []

        # 動態添加過濾條件
        if filters:
            if filters.get("status"):
                query += " AND co.docstatus = %s"
                params.append(filters["status"])
            if filters.get("date_from"):
                query += " AND co.dateordered >= %s"
                params.append(filters["date_from"])
            if filters.get("date_to"):
                query += " AND co.dateordered <= %s"
                params.append(filters["date_to"])
            if filters.get("customer_id"):
                query += " AND co.c_bpartner_id = %s"
                params.append(filters["customer_id"])

        query += """
            GROUP BY co.c_order_id, co.documentno, co.dateordered,
                     co.docstatus, bp.name, co.grandtotal
            ORDER BY co.dateordered DESC
            LIMIT %s
        """
        params.append(limit)

        return self._execute_query(query, params)

    def query_invoices(self, filters=None, limit=100):
        """查詢發票"""
        query = """
            SELECT
                ci.c_invoice_id,
                ci.documentno,
                ci.dateacct,
                ci.docstatus,
                bp.name as customer_name,
                ci.grandtotal,
                COALESCE(SUM(cp.payamt), 0) as paid_amount,
                (ci.grandtotal - COALESCE(SUM(cp.payamt), 0)) as outstanding
            FROM adempiere.c_invoice ci
            LEFT JOIN adempiere.c_bpartner bp ON ci.c_bpartner_id = bp.c_bpartner_id
            LEFT JOIN adempiere.c_payment cp ON ci.c_invoice_id = cp.c_invoice_id
            WHERE 1=1
        """

        params = []

        if filters:
            if filters.get("status"):
                query += " AND ci.docstatus = %s"
                params.append(filters["status"])
            if filters.get("date_from"):
                query += " AND ci.dateacct >= %s"
                params.append(filters["date_from"])
            if filters.get("date_to"):
                query += " AND ci.dateacct <= %s"
                params.append(filters["date_to"])
            if filters.get("min_amount"):
                query += " AND ci.grandtotal >= %s"
                params.append(filters["min_amount"])

        query += """
            GROUP BY ci.c_invoice_id, ci.documentno, ci.dateacct,
                     ci.docstatus, bp.name, ci.grandtotal
            ORDER BY ci.dateacct DESC
            LIMIT %s
        """
        params.append(limit)

        return self._execute_query(query, params)

    def query_products(self, filters=None, limit=100):
        """查詢產品"""
        query = """
            SELECT
                mp.m_product_id,
                mp.value as product_code,
                mp.name as product_name,
                mp.description,
                cu.name as uom_name,
                SUM(COALESCE(ms.qtyonhand, 0)) as total_qty_on_hand,
                COALESCE(AVG(mc.currentcostprice), 0) as unit_cost,
                SUM(COALESCE(ms.qtyonhand, 0)) * COALESCE(AVG(mc.currentcostprice), 0) as inventory_value
            FROM adempiere.m_product mp
            LEFT JOIN adempiere.c_uom cu ON mp.c_uom_id = cu.c_uom_id
            LEFT JOIN adempiere.m_storage ms ON mp.m_product_id = ms.m_product_id
            LEFT JOIN adempiere.m_cost mc ON mp.m_product_id = mc.m_product_id
                AND mc.isactive = 'Y'
            WHERE 1=1
        """

        params = []

        if filters:
            if filters.get("search"):
                query += " AND (mp.name ILIKE %s OR mp.value ILIKE %s)"
                params.extend([f"%{filters['search']}%", f"%{filters['search']}%"])

        query += """
            GROUP BY mp.m_product_id, mp.value, mp.name, mp.description, cu.c_uom_id, cu.name
            ORDER BY inventory_value DESC
            LIMIT %s
        """
        params.append(limit)

        return self._execute_query(query, params)

    def query_customers(self, filters=None, limit=100):
        """查詢客戶"""
        query = """
            SELECT
                bp.c_bpartner_id,
                bp.value as customer_code,
                bp.name as customer_name,
                COALESCE(bp.so_creditlimit, 0) as credit_limit,
                COALESCE(bp.totalopenbalance, 0) as total_open_balance,
                COUNT(DISTINCT co.c_order_id) as order_count,
                SUM(COALESCE(co.grandtotal, 0)) as total_sales
            FROM adempiere.c_bpartner bp
            LEFT JOIN adempiere.c_order co ON bp.c_bpartner_id = co.c_bpartner_id
                                              AND co.docstatus IN ('CO', 'CL')
            WHERE bp.isvendor = 'N'
        """

        params = []

        if filters:
            if filters.get("search"):
                query += " AND (bp.name ILIKE %s OR bp.value ILIKE %s)"
                params.extend([f"%{filters['search']}%", f"%{filters['search']}%"])

        query += """
            GROUP BY bp.c_bpartner_id, bp.value, bp.name, bp.so_creditlimit, bp.totalopenbalance
            ORDER BY total_sales DESC
            LIMIT %s
        """
        params.append(limit)

        return self._execute_query(query, params)

    def query_inventory(self, filters=None, limit=100):
        """查詢庫存（含成本計算）"""
        query = """
            SELECT
                mp.m_product_id,
                mp.value as product_code,
                mp.name as product_name,
                mw.name as warehouse_name,
                ml.value as locator_name,
                SUM(COALESCE(ms.qtyonhand, 0)) as qty_on_hand,
                COALESCE(AVG(mc.currentcostprice), 0) as unit_cost,
                SUM(COALESCE(ms.qtyonhand, 0)) * COALESCE(AVG(mc.currentcostprice), 0) as inventory_value,
                MAX(ms.updated) as last_update
            FROM adempiere.m_storage ms
            INNER JOIN adempiere.m_product mp
                ON ms.m_product_id = mp.m_product_id
            LEFT JOIN adempiere.m_locator ml
                ON ms.m_locator_id = ml.m_locator_id
            LEFT JOIN adempiere.m_warehouse mw
                ON ml.m_warehouse_id = mw.m_warehouse_id
            LEFT JOIN adempiere.m_cost mc
                ON mp.m_product_id = mc.m_product_id
                AND mc.isactive = 'Y'
            WHERE mp.isactive = 'Y'
                AND ms.qtyonhand > 0
        """

        params = []

        if filters:
            if filters.get("warehouse_id"):
                query += " AND mw.m_warehouse_id = %s"
                params.append(filters["warehouse_id"])

        query += """
            GROUP BY
                mp.m_product_id,
                mp.value,
                mp.name,
                mw.m_warehouse_id,
                mw.name,
                ml.m_locator_id,
                ml.value
            ORDER BY inventory_value DESC
            LIMIT %s
        """
        params.append(limit)

        return self._execute_query(query, params)

    def sales_summary(self, date_from=None, date_to=None):
        """銷售摘要統計"""
        query = """
            SELECT
                COUNT(DISTINCT c_order_id) as order_count,
                SUM(grandtotal) as total_sales,
                AVG(grandtotal) as avg_order_value,
                MIN(grandtotal) as min_order_value,
                MAX(grandtotal) as max_order_value
            FROM adempiere.c_order
            WHERE docstatus IN ('CO', 'CL')
        """

        params = []

        if date_from:
            query += " AND dateordered >= %s"
            params.append(date_from)
        if date_to:
            query += " AND dateordered <= %s"
            params.append(date_to)

        result = self._execute_query(query, params)
        return result[0] if result else {}

    def ar_aging(self, days_threshold=30):
        """應收帳齡分析"""
        query = """
            SELECT
                bp.name as customer_name,
                ci.documentno as invoice_no,
                ci.dateacct,
                ci.grandtotal as amount,
                (ci.grandtotal - COALESCE(SUM(cp.payamt), 0)) as outstanding,
                (NOW()::DATE - ci.dateacct) as days_overdue
            FROM adempiere.c_invoice ci
            JOIN adempiere.c_bpartner bp ON ci.c_bpartner_id = bp.c_bpartner_id
            LEFT JOIN adempiere.c_payment cp ON ci.c_invoice_id = cp.c_invoice_id
            WHERE ci.docstatus IN ('CO', 'CL')
            AND (ci.grandtotal - COALESCE(SUM(cp.payamt), 0)) > 0
            GROUP BY ci.c_invoice_id, bp.name, ci.documentno, ci.dateacct, ci.grandtotal
            HAVING (NOW()::DATE - ci.dateacct) >= %s
            ORDER BY days_overdue DESC
        """

        result = self._execute_query(query, [days_threshold])
        return result

    def _execute_query(self, query, params):
        """執行 SQL 查詢並返回結果"""
        try:
            # 確保連接狀態正常
            if not self.conn or self.conn.closed:
                self.connect()

            # 重置連接狀態（防止 "transaction aborted" 錯誤）
            self.conn.rollback()

            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, params)
            results = cursor.fetchall()
            cursor.close()

            # 提交事務
            self.conn.commit()

            # 轉換為 JSON 序列化格式
            return [dict(row) for row in results]
        except Exception as e:
            print(f"❌ Query failed: {e}")
            # 嘗試重新連接
            try:
                if self.conn:
                    self.conn.rollback()
                self.close()
                self.connect()
            except:
                pass
            return []

    def execute_custom_query(self, sql, params=None):
        """
        執行自定義 SQL 查詢

        使用場景：更複雜的查詢邏輯
        """
        if params is None:
            params = []
        return self._execute_query(sql, params)


# 全局工具實例
db_tool = DatabaseTool()


def init_db():
    """初始化資料庫連接"""
    db_tool.connect()


def close_db():
    """關閉資料庫連接"""
    db_tool.close()


if __name__ == "__main__":
    # 測試用
    init_db()

    print("\n📊 Testing Sales Orders Query:")
    orders = db_tool.query_sales_orders(limit=5)
    print(f"Found {len(orders)} orders")
    for order in orders:
        print(f"  - {order['documentno']}: {order['grandtotal']} (Status: {order['docstatus']})")

    print("\n📊 Testing Products Query:")
    products = db_tool.query_products(limit=5)
    print(f"Found {len(products)} products")
    for product in products:
        print(f"  - {product['product_code']}: {product['product_name']} (Qty: {product['total_qty_on_hand']})")

    print("\n📊 Sales Summary:")
    summary = db_tool.sales_summary()
    print(json.dumps(summary, indent=2, default=str))

    close_db()
