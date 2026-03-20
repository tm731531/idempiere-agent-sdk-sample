"""
Data Recovery Layer - Restore masked values based on user permissions
"""

import re
from typing import Dict
from .masking import DataMaskingEngine


class DataRecoveryLayer:
    """Recover masked data based on user permissions"""

    def __init__(self, masking_engine: DataMaskingEngine):
        self.engine = masking_engine


    def restore_response(self, response: str, user_id: str, permission_level: str) -> str:
        """
        Restore masked values in response based on user permissions

        Example:
        Input:  "客戶 CUST_A1B2C3D4 欠款 $50,000，逾期 35 天"
        Output (if manager): "客戶 ABC Corp 欠款 $50,000，逾期 35 天"
        Output (if viewer):  "客戶 CUST_A1B2C3D4 欠款 $50,000，逾期 35 天"
        """

        # Viewer can't unmask
        if permission_level == 'viewer':
            return response

        # Find all masked values (pattern: CUST_*)
        masked_pattern = r'CUST_[A-F0-9]+'
        matches = re.finditer(masked_pattern, response)

        restored_response = response
        recovery_stats = {'attempted': 0, 'succeeded': 0, 'denied': 0}

        for match in matches:
            masked_value = match.group()
            recovery_stats['attempted'] += 1

            try:
                original_value = self.engine.unmask_value(
                    masked_value,
                    user_id,
                    permission_level
                )
                # Replace masked value with original
                restored_response = restored_response.replace(masked_value, original_value)
                recovery_stats['succeeded'] += 1
                print(f"[RECOVERY] ✅ {masked_value} → {original_value}")

            except PermissionError as e:
                recovery_stats['denied'] += 1
                print(f"[RECOVERY] ❌ {masked_value} (Permission Denied)")

        print(f"\n[SUMMARY] Recovered {recovery_stats['succeeded']}/{recovery_stats['attempted']} values")

        return restored_response


    def restore_dict(self, data: Dict, user_id: str, permission_level: str) -> Dict:
        """
        Restore masked values in dictionary

        Args:
            data: Dictionary with masked values
            user_id: User ID
            permission_level: Permission level

        Returns:
            Dictionary with restored values (where permitted)
        """
        restored = data.copy()

        # Find and restore all masked values
        masked_pattern = r'CUST_[A-F0-9]+'

        for key, value in data.items():
            if isinstance(value, str):
                matches = re.finditer(masked_pattern, value)
                for match in matches:
                    masked_value = match.group()
                    try:
                        original_value = self.engine.unmask_value(
                            masked_value,
                            user_id,
                            permission_level
                        )
                        restored[key] = value.replace(masked_value, original_value)
                    except PermissionError:
                        pass

        return restored
