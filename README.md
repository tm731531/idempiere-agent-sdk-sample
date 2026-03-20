# iDempiere Agent SDK - 商業智能助手

用 **Claude Agent SDK** 讓 iDempiere 資料純粹說話。擺脫 ZK UI，用自然語言查詢和分析你的業務資料。

## 🎯 功能特性

### 智能查詢助手
- 用自然語言提問，Agent 自動選擇正確的表和 JOIN
- 支持複雜的業務邏輯（過濾、排序、聚合）
- 無限種提問方式，同一個工具自動應對

### 實時分析
- 銷售摘要統計
- 應收帳齡分析
- 庫存狀態查詢
- 客戶分析

### 自然語言界面
- 無需學習 SQL
- 支持中文自然表達
- 自動理解業務術語

## 📋 快速開始

### 1. 安裝依賴

```bash
cd ~/idempiere-agent-web

# 建立 Python 虛擬環境
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate     # Windows

# 安裝依賴
pip install -r requirements.txt
```

### 2. 配置環境變數

編輯 `.env` 文件：

```env
# iDempiere Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=idempiere
DB_USER=adempiere
DB_PASSWORD=adempiere

# Claude API Key (從 https://console.anthropic.com 獲取)
ANTHROPIC_API_KEY=your_api_key_here
```

### 3. 運行應用

```bash
python app.py
```

輸出應該顯示：
```
 * Running on http://0.0.0.0:5000
```

### 4. 打開網頁

在瀏覽器訪問：
```
http://localhost:5000
```

## 🧠 Agent Tools（可用的工具）

### 1. query_sales_orders
查詢銷售訂單
```
用戶: "3月的訂單有哪些？"
→ 自動過濾 dateordered >= 2026-03-01
```

### 2. query_invoices
查詢發票
```
用戶: "超過 $5000 的發票列表"
→ 自動過濾 grandtotal > 5000
```

### 3. query_products
查詢產品和庫存
```
用戶: "告訴我庫存最多的產品"
→ 查詢所有產品，按庫存排序
```

### 4. query_customers
查詢客戶和銷售統計
```
用戶: "我的頂級客戶是誰？"
→ 按銷售額排序客戶
```

### 5. query_inventory
詳細庫存查詢
```
用戶: "倉庫 A 現在有多少產品？"
→ 按倉庫過濾
```

### 6. sales_summary
銷售摘要統計
```
用戶: "給我本月的銷售統計"
→ 返回訂單數、銷售額、平均值
```

### 7. ar_aging
應收帳齡分析
```
用戶: "哪些客戶欠款超過 30 天？"
→ 自動識別逾期應收
```

## 💡 使用範例

### 例 1：銷售分析
```
用戶: "今月銷售額最高的產品是什麼？"

Agent 流程：
  1. 理解：需要查詢本月銷售數據
  2. 決定：調用 query_sales_orders + product data
  3. 執行：JOIN 表、過濾日期、聚合
  4. 回答："根據本月訂單，產品 XYZ 銷售額最高，$45,200"
```

### 例 2：風險檢測
```
用戶: "有多少未付款的發票？"

Agent 流程：
  1. 理解：需要查詢未付款發票
  2. 決定：調用 query_invoices + ar_aging
  3. 執行：查詢、計算金額
  4. 回答："8 張未付款發票，總計 $89,600，其中 3 張已逾期"
```

### 例 3：庫存優化
```
用戶: "哪些產品庫存超過 3 個月沒有銷售？"

Agent 流程：
  1. 理解：需要檢測滯銷品
  2. 決定：調用 query_inventory + movement history
  3. 執行：查詢、計算天數
  4. 回答："5 個產品滯銷，建議清倉處理"
```

## 📊 資料庫連接

應用自動連接到本地 iDempiere PostgreSQL：

```
Host: localhost:5432
Database: idempiere
User: adempiere
Password: adempiere
```

確保 PostgreSQL 運行且資料庫可訪問：

```bash
PGPASSWORD=adempiere psql -h localhost -U adempiere -d idempiere -c "SELECT COUNT(*) FROM adempiere.c_order;"
```

## 🔧 故障排除

### 連接資料庫失敗
```bash
# 檢查 PostgreSQL 是否運行
sudo systemctl status postgresql

# 驗證憑據
PGPASSWORD=adempiere psql -h localhost -U adempiere -d idempiere -c "SELECT 1"
```

### Claude API 錯誤
- 確認 `ANTHROPIC_API_KEY` 已設置在 `.env`
- 檢查 API 密鑰是否有效（https://console.anthropic.com）
- 檢查網絡連接

### 頁面無法加載
- 確認應用運行在 `http://localhost:5000`
- 檢查防火牆設置
- 查看控制台日誌

## 📈 後續計劃

### Phase 1（已完成）
- ✅ 基本查詢工具
- ✅ Web UI
- ✅ Agent 迴圈

### Phase 2（計劃中）
- 📋 報表生成工具
- ⚠️ 異常檢測工具
- 📊 高級分析工具

### Phase 3（後續）
- 🔔 自動告警系統
- 📤 匯出功能（Excel、PDF）
- 🌐 多語言支持

## 🎨 開發

### 項目結構

```
idempiere-agent-web/
├── app.py                    # Flask 主程序
├── config.py                 # 配置
├── tools/
│   ├── __init__.py
│   ├── database.py           # 資料庫工具
│   ├── reports.py            # 報表工具（計劃中）
│   └── anomalies.py          # 異常檢測（計劃中）
├── templates/
│   └── index.html            # Web UI
├── static/                   # 靜態文件（CSS、JS）
├── requirements.txt
├── .env                      # 環境變數
└── README.md                 # 本文件
```

### 添加新工具

在 `tools/` 目錄建立新文件：

```python
# tools/my_tool.py
def my_function(param1, param2):
    """我的新工具描述"""
    # 實現邏輯
    return result
```

在 `app.py` 中：

```python
# 1. 添加 Tool 定義
TOOLS.append({
    "name": "my_tool",
    "description": "...",
    "input_schema": {...}
})

# 2. 在 execute_tool() 中添加邏輯
elif tool_name == "my_tool":
    result = my_function(...)
```

## 📝 日誌

應用記錄詳細的執行日誌，包括：
- Agent 迭代次數
- 工具調用紀錄
- 查詢執行時間
- 錯誤信息

## ⚖️ 注意事項

- 所有查詢都是 **只讀的**，不修改資料庫
- Agent 的回答基於實時資料
- 複雜查詢可能需要多個 Agent 迭代
- API 使用會產生 Claude API 費用

## 📚 參考資料

- [Claude API 文檔](https://docs.anthropic.com)
- [iDempiere 文檔](https://wiki.idempiere.org)
- [PostgreSQL 文檔](https://www.postgresql.org/docs/)

## 🤝 貢獻

歡迎提交問題和改進建議！

## 📄 License

MIT License

---

**Created**: 2026-03-20
**Status**: Beta
**Powered by Claude Agent SDK**
