# iDempiere Agent SDK - 詳細設置指南

## ✅ 系統已準備好！

完整的 iDempiere Agent SDK 應用已建立在 `/home/tom/idempiere-agent-web/`

## 🚀 快速啟動（3 分鐘）

### Step 1: 設置 API 密鑰

編輯 `.env` 文件並設置你的 Claude API 密鑰：

```bash
cd ~/idempiere-agent-web
nano .env
```

**需要修改的項目**：
```env
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx  # 替換為你的 API 密鑰
```

其他配置已正確設置為你的本地 iDempiere 資料庫。

### Step 2: 啟動應用

#### 方法 1：使用快速啟動腳本（推薦）

```bash
cd ~/idempiere-agent-web
chmod +x start.sh
./start.sh
```

#### 方法 2：手動啟動

```bash
cd ~/idempiere-agent-web
source venv/bin/activate
python3 app.py
```

### Step 3: 打開網頁

訪問 http://localhost:5000

```
🌐 在瀏覽器打開：
   http://localhost:5000

   或 (遠程訪問)：
   http://[your_ip]:5000
```

## 📊 開始提問

### 範例提問

```
1️⃣ "今月銷售額最高的產品是什麼？"
   → Agent 自動查詢、分析、回答

2️⃣ "我有多少未付款的發票？"
   → 自動檢測應收欠款

3️⃣ "當前庫存總值是多少？"
   → 計算所有產品的庫存價值

4️⃣ "超過 30 天未付款的發票有哪些？"
   → 帳齡分析

5️⃣ "誰是我最大的客戶？"
   → 客戶銷售排名
```

## 🎯 了解工作原理

### Agent 執行流程

```
用戶提問
    ↓
1️⃣ Flask 接收問題 (/api/chat)
    ↓
2️⃣ Claude Agent 分析問題
    ├─ 理解業務意圖
    └─ 決定需要哪些工具
    ↓
3️⃣ 執行 Agent Tools
    ├─ query_sales_orders()
    ├─ query_invoices()
    ├─ query_products()
    ├─ query_customers()
    ├─ query_inventory()
    ├─ sales_summary()
    └─ ar_aging()
    ↓
4️⃣ 查詢 iDempiere PostgreSQL
    ├─ 自動 JOIN 相關表
    ├─ 過濾、排序、聚合
    └─ 返回結構化結果
    ↓
5️⃣ Claude 整合結果
    ├─ 分析數據
    ├─ 生成見解
    └─ 用自然語言回答
    ↓
6️⃣ 返回給用戶
    └─ 顯示在 Web 界面
```

## 🔧 項目結構

```
idempiere-agent-web/
├── 📄 app.py                    (Flask 主程序 - 250 行)
├── 📄 config.py                 (配置文件 - 150 行)
├── 📄 start.sh                  (快速啟動腳本)
├── 📄 README.md                 (說明文檔)
├── 📄 SETUP_GUIDE.md            (本文件)
├── 📄 requirements.txt           (Python 依賴)
├── 📄 .env                      (環境變數配置)
│
├── 📁 tools/                    (Agent Tools)
│   ├── __init__.py
│   └── database.py              (資料庫查詢工具 - 350 行)
│
├── 📁 templates/                (Web 界面)
│   └── index.html               (前端頁面 - 350 行)
│
├── 📁 static/                   (靜態文件 - 待擴展)
│   ├── css/
│   └── js/
│
└── 📁 venv/                     (Python 虛擬環境 - 自動建立)
```

### 代碼統計

```
✅ Flask 應用: 250 行
✅ 資料庫工具: 350 行
✅ 前端界面: 350 行
✅ 配置文件: 150 行
────────────────────
   總計: ~1100 行代碼
```

## 🛠️ 工具詳解

### Tool: query_sales_orders()
查詢銷售訂單（C_Order 表）

**支持的過濾**：
- `status`: 訂單狀態 (DR/CO/CL)
- `date_from`: 起始日期
- `date_to`: 終止日期
- `customer_id`: 特定客戶

**返回字段**：
- 訂單編號、日期、狀態
- 客戶名稱
- 訂單金額
- 行項目數

### Tool: query_invoices()
查詢發票（C_Invoice 表）

**支持的過濾**：
- `status`: 發票狀態
- `date_from/date_to`: 日期範圍
- `min_amount`: 最小金額

**自動計算**：
- 已付款金額
- 未付款餘額

### Tool: ar_aging()
應收帳齡分析

**自動識別**：
- 逾期應收（>30 天）
- 即期應收
- 逾期天數

### Tool: sales_summary()
銷售摘要統計

**自動計算**：
- 訂單總數
- 銷售總額
- 平均訂單值
- 最高/最低訂單值

### Tool: 其他工具
- `query_products()` - 產品及庫存
- `query_customers()` - 客戶銷售分析
- `query_inventory()` - 庫存詳情

## 🎓 Advanced 用法

### 1. 自定義 SQL 查詢

如果內置工具不足以應對，Agent 可以要求執行自定義 SQL：

```python
# 在 database.py 中
def execute_custom_query(self, sql, params=None):
    """執行自定義 SQL 查詢"""
    return self._execute_query(sql, params)
```

### 2. 延伸 Prompt 指令

編輯 `app.py` 中的 `system_prompt` 來改變 Agent 的行為：

```python
system_prompt = """
你是一個 iDempiere 商業智能助手...
[自定義你的指導原則]
"""
```

### 3. 添加新工具

在 `tools/database.py` 中添加新方法，然後在 `app.py` 中：

```python
# 1. 添加 Tool 定義
TOOLS.append({
    "name": "my_new_tool",
    "description": "描述",
    "input_schema": {...}
})

# 2. 在 execute_tool() 中處理
elif tool_name == "my_new_tool":
    result = db_tool.my_new_tool(...)
```

## 📊 數據庫連接檢驗

### 驗證連接

```bash
# 測試 PostgreSQL 連接
PGPASSWORD=adempiere psql -h localhost -U adempiere -d idempiere -c "SELECT COUNT(*) FROM adempiere.c_order;"

# 應該輸出類似：
#  count
# -------
#     33
```

### 查看可用數據

```bash
# iDempiere 資料庫統計
PGPASSWORD=adempiere psql -h localhost -U adempiere -d idempiere << EOF
SELECT
  (SELECT COUNT(*) FROM adempiere.c_order) as orders,
  (SELECT COUNT(*) FROM adempiere.c_invoice) as invoices,
  (SELECT COUNT(*) FROM adempiere.m_product) as products,
  (SELECT COUNT(*) FROM adempiere.c_bpartner) as partners,
  (SELECT COUNT(*) FROM adempiere.m_storage) as inventory_lines;
EOF
```

## 🐛 故障排除

### 問題 1: "Database connection failed"

```bash
# 檢查 PostgreSQL 運行狀態
sudo systemctl status postgresql

# 驗證憑據
PGPASSWORD=adempiere psql -h localhost -U adempiere -d idempiere -c "SELECT 1"
```

### 問題 2: "ANTHROPIC_API_KEY not found"

```bash
# 確認 .env 文件存在且包含 API 密鑰
cat .env | grep ANTHROPIC_API_KEY

# 或重新建立
echo "ANTHROPIC_API_KEY=your_key_here" >> .env
```

### 問題 3: Port 5000 已在使用

```bash
# 找出占用 port 5000 的程序
lsof -i :5000

# 終止該程序或使用不同的 port
# 編輯 app.py，改變 port：
# app.run(host="0.0.0.0", port=5001)
```

### 問題 4: Agent 回答很慢

```bash
# 可能是：
# 1. Claude API 延遲 - 正常（2-3 秒）
# 2. 複雜查詢 - Agent 可能需要多次迭代
# 3. 資料庫性能 - 檢查查詢執行時間

# 在日誌中查看：
# [Iteration 1: Calling Claude...]
# [Executing tool: query_sales_orders]
```

## 📈 性能優化

### 1. 數據庫索引

確保關鍵字段有索引（iDempiere 已配置）：

```sql
-- 檢查索引
\d adempiere.c_order
\d adempiere.m_product
```

### 2. 查詢快取

可以在 `database.py` 中添加簡單的快取：

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_product_list():
    """可快取的查詢"""
    ...
```

### 3. 連接池

生產環境建議使用連接池：

```python
# 在 config.py 中配置
import psycopg2.pool

db_pool = psycopg2.pool.SimpleConnectionPool(1, 20, **DB_CONFIG)
```

## 🚢 部署建議

### 本地開發

```bash
./start.sh
# 自動啟用調試模式，Auto-reload
```

### 本地生產

```bash
# 關閉調試模式
FLASK_ENV=production python3 app.py
```

### Docker 部署（計劃中）

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python3", "app.py"]
```

### systemd 服務（計劃中）

```ini
[Unit]
Description=iDempiere Agent SDK
After=network.target

[Service]
Type=simple
User=tom
WorkingDirectory=/home/tom/idempiere-agent-web
Environment="PATH=/home/tom/idempiere-agent-web/venv/bin"
ExecStart=/home/tom/idempiere-agent-web/venv/bin/python3 app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## 📚 下一步

### 短期（本週）
- ✅ 完成基本的查詢工具
- ✅ Web UI 上線
- 🔲 測試各種提問方式

### 中期（1-2 週）
- 🔲 添加報表生成工具
- 🔲 實現異常檢測工具
- 🔲 優化 Prompt 和響應

### 長期（1 個月）
- 🔲 自動告警系統
- 🔲 多語言支持
- 🔲 與 SimpleEC OMS 整合

## 💬 反饋和改進

遇到問題或有建議？

1. 檢查日誌輸出（`/tmp/idempiere_agent.log`）
2. 查閱故障排除部分
3. 提交問題報告

## 📞 技術支持

開發環境：
- Python 3.12.3 ✅
- PostgreSQL 16 ✅
- Claude API (Opus 4.6) ✅
- iDempiere 12.0 ✅

---

**祝你好運！🚀**

開始提問，讓 Claude 為你分析業務數據吧！

**访问地址**: http://localhost:5000
