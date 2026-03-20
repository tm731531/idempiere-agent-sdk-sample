#!/usr/bin/env python3
"""
Demo: Data Masking and Recovery with Permission Control

演示脫敏和恢復流程，包含不同權限級別
"""

import json
from privacy.masking import DataMaskingEngine
from privacy.recovery import DataRecoveryLayer


def print_section(title: str):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def demo_basic_masking():
    """Demo 1: Basic data masking"""
    print_section("Demo 1: 基本脫敏")

    # Initialize engine
    engine = DataMaskingEngine()

    # Original invoice data (sensitive)
    original_invoice = {
        'c_invoice_id': 12345,
        'documentno': 'INV-2026-001',
        'customer_name': 'ABC Corp',
        'customer_phone': '+886-2-1234-5678',
        'customer_email': 'sales@abc.com',
        'amount': 50000,
        'dateacct': '2026-03-20',
        'docstatus': 'CO',
        'outstanding': 50000,
        'days_overdue': 35
    }

    print("【原始資料】（敏感）")
    print(json.dumps(original_invoice, indent=2, ensure_ascii=False))

    # Mask the invoice
    masked_invoice = engine.mask_invoice(original_invoice)

    print("\n【脫敏後資料】（可安全傳給 Claude）")
    print(json.dumps(masked_invoice, indent=2, ensure_ascii=False))

    print("\n【加密映射表】（本地密鑰管理）")
    for key, value in engine.mappings.items():
        print(f"  {key}")
        print(f"    → 加密資料: {value['encrypted'][:50]}...")
        print(f"    → 欄位: {value['field']}")

    return engine, original_invoice, masked_invoice


def demo_recovery_with_permissions():
    """Demo 2: Data recovery with permission control"""
    print_section("Demo 2: 基於權限的恢復")

    # Create engine and mask data
    engine = DataMaskingEngine()

    # Mask a customer name
    masked_name, record = engine.mask_customer_name("ABC Corp")
    print(f"【脫敏結果】")
    print(f"  原始值: ABC Corp")
    print(f"  脫敏值: {masked_name}\n")

    # Simulate LLM analysis with masked data
    llm_response = f"客戶 {masked_name} 欠款 $50,000，逾期 35 天。建議立即跟進催款。"
    print(f"【Claude 分析結果】（只看脫敏資料）")
    print(f"  {llm_response}\n")

    # Test recovery with different permission levels
    test_cases = [
        ('admin_001', 'admin', '管理員'),
        ('mgr_001', 'manager', '經理'),
        ('analyst_001', 'analyst', '分析師'),
        ('viewer_001', 'viewer', '檢視員'),
    ]

    recovery_layer = DataRecoveryLayer(engine)

    for user_id, perm_level, user_type in test_cases:
        print(f"\n【{user_type} ({perm_level})】")
        try:
            restored = recovery_layer.restore_response(
                llm_response,
                user_id,
                perm_level
            )
            print(f"  結果: {restored}")
        except PermissionError as e:
            print(f"  錯誤: {e}")


def demo_invoice_masking_chain():
    """Demo 3: Complete invoice masking-analysis-recovery chain"""
    print_section("Demo 3: 完整流程 - 脫敏→分析→恢復")

    engine = DataMaskingEngine()
    recovery_layer = DataRecoveryLayer(engine)

    # Sample invoices
    invoices = [
        {
            'c_invoice_id': 1001,
            'documentno': 'INV-001',
            'customer_name': 'ABC Corp',
            'customer_phone': '+886-2-1234-5678',
            'customer_email': 'sales@abc.com',
            'amount': 50000,
            'outstanding': 50000,
            'days_overdue': 35
        },
        {
            'c_invoice_id': 1002,
            'documentno': 'INV-002',
            'customer_name': 'XYZ Ltd',
            'customer_phone': '+886-3-9876-5432',
            'customer_email': 'info@xyz.com',
            'amount': 75000,
            'outstanding': 75000,
            'days_overdue': 45
        }
    ]

    print("【Step 1: 原始發票資料（敏感）】")
    for invoice in invoices:
        print(f"  {invoice['documentno']}: {invoice['customer_name']} - ${invoice['amount']}")

    # Mask invoices
    masked_invoices = [engine.mask_invoice(inv) for inv in invoices]

    print("\n【Step 2: 脫敏後發票資料（脫敏，可安全上雲）】")
    for masked in masked_invoices:
        print(f"  {masked['documentno']}: {masked['customer_name']} - ${masked['amount']}")

    # Simulate Claude analysis
    llm_analysis = f"""
【應收帳齡分析】

逾期應收超過 30 天的發票：

1. {masked_invoices[0]['documentno']}
   - 客戶: {masked_invoices[0]['customer_name']}
   - 金額: ${masked_invoices[0]['amount']}
   - 逾期: {masked_invoices[0]['days_overdue']} 天
   - 建議: 立即催款

2. {masked_invoices[1]['documentno']}
   - 客戶: {masked_invoices[1]['customer_name']}
   - 金額: ${masked_invoices[1]['amount']}
   - 逾期: {masked_invoices[1]['days_overdue']} 天
   - 建議: 嚴肅跟進，考慮法律途徑
"""

    print("\n【Step 3: Claude 分析結果（脫敏版）】")
    print(llm_analysis)

    # Recover with manager permission
    print("\n【Step 4: 經理權限恢復】")
    restored = recovery_layer.restore_response(
        llm_analysis,
        user_id='mgr_001',
        permission_level='manager'
    )
    print("\n恢復後的報告:")
    print(restored)

    # Show audit log
    print("\n【稽核日誌】")
    for entry in engine.get_audit_log():
        print(f"  [{entry['timestamp']}] {entry['user_id']}: {entry['status']}")


def demo_audit_trail():
    """Demo 4: Audit trail - Who accessed what"""
    print_section("Demo 4: 稽核日誌")

    engine = DataMaskingEngine()

    # Mask customer name
    masked_name, _ = engine.mask_customer_name("ABC Corp")

    # Multiple users trying to access
    test_accesses = [
        ('admin_001', 'admin'),
        ('mgr_001', 'manager'),
        ('analyst_001', 'analyst'),
        ('viewer_001', 'viewer'),
    ]

    print(f"脫敏值: {masked_name}\n")

    for user_id, perm_level in test_accesses:
        try:
            engine.unmask_value(masked_name, user_id, perm_level)
        except PermissionError:
            pass  # Expected for viewer

    # Display audit log
    print("【完整稽核日誌】\n")
    print(f"{'時間':<25} {'使用者':<12} {'動作':<15} {'狀態':<10}")
    print("-" * 65)

    for entry in engine.get_audit_log():
        print(f"{entry['timestamp']:<25} {entry['user_id']:<12} {entry['action']:<15} {entry['status']:<10}")


def main():
    """Run all demos"""
    print("\n" + "="*60)
    print("  iDempiere Agent SDK: 脫敏和恢復演示")
    print("="*60)

    # Demo 1: Basic masking
    engine, original, masked = demo_basic_masking()

    # Demo 2: Permission-based recovery
    demo_recovery_with_permissions()

    # Demo 3: Complete chain
    demo_invoice_masking_chain()

    # Demo 4: Audit trail
    demo_audit_trail()

    # Summary
    print_section("總結")
    print("""
✅ 關鍵點：

1. 【脫敏】敏感資料自動被遮罩/加密
   - 客戶名稱: ABC Corp → CUST_A1B2C3D4
   - 電話: +886-2-1234-5678 → +886-***-****-****
   - 金額、日期等業務資料保留

2. 【分析】Claude 只看脫敏資料
   - 無法識別真實客戶身份
   - 只能基於數字和日期分析
   - 完全符合隱私法規

3. 【恢復】根據權限恢復原始資料
   - Admin: 可看所有原始資料
   - Manager: 可看客戶名稱、聯絡方式
   - Analyst: 只看脫敏資料
   - Viewer: 必須看脫敏資料

4. 【稽核】所有恢復操作都被記錄
   - 誰、何時、訪問了什麼
   - 用於合規性審計
   - 不可否認性

🔒 隱私保證：
   • 資料離開本地前必須脫敏
   • Claude 無法識別真實身份
   • 恢復過程有權限控制
   • 完整的審計追蹤
""")

    print("\n" + "="*60)
    print("演示完成！")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
