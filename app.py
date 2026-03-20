"""
iDempiere Agent SDK Web Application
Main Flask application with Claude Agent SDK integration
"""
import json
import logging
from flask import Flask, render_template, request, jsonify
from anthropic import Anthropic
from tools.database import db_tool, init_db, close_db
from config import CLAUDE_MODEL, CLAUDE_MAX_TOKENS

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize database
@app.before_request
def setup():
    if not hasattr(app, 'db_initialized'):
        init_db()
        app.db_initialized = True

@app.teardown_appcontext
def shutdown(exception=None):
    pass  # Connection pooling handles cleanup

# Initialize Anthropic client
client = Anthropic()

# Tool definitions for Claude
TOOLS = [
    {
        "name": "query_sales_orders",
        "description": "查詢銷售訂單。支持按狀態、日期、客戶過濾",
        "input_schema": {
            "type": "object",
            "properties": {
                "filters": {
                    "type": "object",
                    "description": "過濾條件",
                    "properties": {
                        "status": {"type": "string", "description": "訂單狀態 (DR/CO/CL)"},
                        "date_from": {"type": "string", "description": "起始日期 (YYYY-MM-DD)"},
                        "date_to": {"type": "string", "description": "終止日期 (YYYY-MM-DD)"},
                        "customer_id": {"type": "integer", "description": "客戶 ID"}
                    }
                },
                "limit": {
                    "type": "integer",
                    "description": "返回筆數，默認 100",
                    "default": 100
                }
            }
        }
    },
    {
        "name": "query_invoices",
        "description": "查詢發票。支持按狀態、日期、金額過濾",
        "input_schema": {
            "type": "object",
            "properties": {
                "filters": {
                    "type": "object",
                    "description": "過濾條件",
                    "properties": {
                        "status": {"type": "string", "description": "發票狀態 (CO/CL)"},
                        "date_from": {"type": "string", "description": "起始日期 (YYYY-MM-DD)"},
                        "date_to": {"type": "string", "description": "終止日期 (YYYY-MM-DD)"},
                        "min_amount": {"type": "number", "description": "最小金額"}
                    }
                },
                "limit": {
                    "type": "integer",
                    "description": "返回筆數，默認 100",
                    "default": 100
                }
            }
        }
    },
    {
        "name": "query_products",
        "description": "查詢產品及庫存。支持按名稱搜尋",
        "input_schema": {
            "type": "object",
            "properties": {
                "filters": {
                    "type": "object",
                    "description": "過濾條件",
                    "properties": {
                        "search": {"type": "string", "description": "產品名稱或代碼搜尋"}
                    }
                },
                "limit": {
                    "type": "integer",
                    "description": "返回筆數，默認 100",
                    "default": 100
                }
            }
        }
    },
    {
        "name": "query_customers",
        "description": "查詢客戶及銷售統計",
        "input_schema": {
            "type": "object",
            "properties": {
                "filters": {
                    "type": "object",
                    "description": "過濾條件",
                    "properties": {
                        "search": {"type": "string", "description": "客戶名稱或代碼搜尋"}
                    }
                },
                "limit": {
                    "type": "integer",
                    "description": "返回筆數，默認 100",
                    "default": 100
                }
            }
        }
    },
    {
        "name": "query_inventory",
        "description": "查詢庫存資訊。支持按倉庫過濾",
        "input_schema": {
            "type": "object",
            "properties": {
                "filters": {
                    "type": "object",
                    "description": "過濾條件",
                    "properties": {
                        "warehouse_id": {"type": "integer", "description": "倉庫 ID"},
                        "low_stock": {"type": "boolean", "description": "只顯示低庫存"}
                    }
                },
                "limit": {
                    "type": "integer",
                    "description": "返回筆數，默認 100",
                    "default": 100
                }
            }
        }
    },
    {
        "name": "sales_summary",
        "description": "獲取銷售摘要統計（訂單數、銷售額、平均值等）",
        "input_schema": {
            "type": "object",
            "properties": {
                "date_from": {
                    "type": "string",
                    "description": "起始日期 (YYYY-MM-DD)，可選"
                },
                "date_to": {
                    "type": "string",
                    "description": "終止日期 (YYYY-MM-DD)，可選"
                }
            }
        }
    },
    {
        "name": "ar_aging",
        "description": "應收帳齡分析（逾期應收明細）",
        "input_schema": {
            "type": "object",
            "properties": {
                "days_threshold": {
                    "type": "integer",
                    "description": "超過幾天才算逾期，默認 30 天",
                    "default": 30
                }
            }
        }
    }
]


def execute_tool(tool_name: str, tool_input: dict) -> str:
    """執行 Agent 調用的工具"""
    try:
        if tool_name == "query_sales_orders":
            result = db_tool.query_sales_orders(
                filters=tool_input.get("filters"),
                limit=tool_input.get("limit", 100)
            )
        elif tool_name == "query_invoices":
            result = db_tool.query_invoices(
                filters=tool_input.get("filters"),
                limit=tool_input.get("limit", 100)
            )
        elif tool_name == "query_products":
            result = db_tool.query_products(
                filters=tool_input.get("filters"),
                limit=tool_input.get("limit", 100)
            )
        elif tool_name == "query_customers":
            result = db_tool.query_customers(
                filters=tool_input.get("filters"),
                limit=tool_input.get("limit", 100)
            )
        elif tool_name == "query_inventory":
            result = db_tool.query_inventory(
                filters=tool_input.get("filters"),
                limit=tool_input.get("limit", 100)
            )
        elif tool_name == "sales_summary":
            result = db_tool.sales_summary(
                date_from=tool_input.get("date_from"),
                date_to=tool_input.get("date_to")
            )
        elif tool_name == "ar_aging":
            result = db_tool.ar_aging(
                days_threshold=tool_input.get("days_threshold", 30)
            )
        else:
            result = {"error": f"Unknown tool: {tool_name}"}

        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        return json.dumps({"error": str(e)})


def run_agent(user_message: str) -> str:
    """
    執行 Agent 迴圈（Claude Agent SDK 邏輯）

    流程：
    1. 用戶提問
    2. Claude 分析並決定調用哪些工具
    3. 執行工具
    4. 將結果反饋給 Claude
    5. Claude 生成最終回答
    """
    messages = [
        {
            "role": "user",
            "content": user_message
        }
    ]

    system_prompt = """你是一個 iDempiere 商業智能助手。

【回答格式要求 - 非常重要】
簡潔清晰，避免冗長：
- ✓ 用短句和要點列表
- ✓ 數字用簡單的表格或列表
- ✓ 最多用 1-2 個段落解釋
- ✗ 不要用複雜的 Markdown
- ✗ 不要過度修飾或冗餘

【範例格式】
"當前庫存狀況：
- 有庫存產品：22 項
- 零庫存產品：74 項
- 總庫存數量：1,286 件

低庫存警示：
- Azalea Bush（5 件）
- Grass Seeder（8 件）
- Holly Bush（10 件）

建議：補充低庫存產品"

你的角色：
- 幫助用戶理解業務資料
- 提供見解和建議
- 檢測和警告異常

可用工具：
1. query_sales_orders - 銷售訂單
2. query_invoices - 發票
3. query_products - 產品和庫存
4. query_customers - 客戶
5. query_inventory - 庫存詳情
6. sales_summary - 銷售統計
7. ar_aging - 應收帳齡"""

    # Agent 迴圈
    max_iterations = 5
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        logger.info(f"Iteration {iteration}: Calling Claude...")

        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=CLAUDE_MAX_TOKENS,
            system=system_prompt,
            tools=TOOLS,
            messages=messages
        )

        logger.info(f"Stop reason: {response.stop_reason}")

        # 檢查是否完成
        if response.stop_reason == "end_turn":
            # 提取最終回應
            final_response = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_response += block.text
            return final_response

        # 檢查是否需要執行工具
        if response.stop_reason == "tool_use":
            # 執行所有工具調用
            tool_results = []
            assistant_message_content = list(response.content)

            for block in response.content:
                if block.type == "tool_use":
                    logger.info(f"Executing tool: {block.name}")
                    tool_result = execute_tool(block.name, block.input)

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": tool_result
                    })

            # 添加 Assistant 回應和工具結果到消息歷史
            messages.append({
                "role": "assistant",
                "content": assistant_message_content
            })
            messages.append({
                "role": "user",
                "content": tool_results
            })
        else:
            # 其他停止原因
            logger.warning(f"Unexpected stop reason: {response.stop_reason}")
            break

    return "❌ Agent 未能在規定迭代內完成任務"


# Routes
@app.route("/")
def index():
    """首頁"""
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    """聊天 API 端點"""
    try:
        data = request.json
        user_message = data.get("message", "").strip()

        if not user_message:
            return jsonify({"error": "Message is required"}), 400

        logger.info(f"User message: {user_message}")

        # 運行 Agent
        response = run_agent(user_message)

        return jsonify({
            "response": response,
            "status": "success"
        })

    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500


@app.route("/api/health", methods=["GET"])
def health():
    """健康檢查"""
    return jsonify({
        "status": "healthy",
        "message": "iDempiere Agent SDK is running"
    })


if __name__ == "__main__":
    logger.info("🚀 Starting iDempiere Agent SDK Web Application...")
    logger.info(f"   Model: {CLAUDE_MODEL}")
    logger.info(f"   Max Tokens: {CLAUDE_MAX_TOKENS}")
    logger.info(f"   Tools: {len(TOOLS)}")

    app.run(host="0.0.0.0", port=5000, debug=True)
