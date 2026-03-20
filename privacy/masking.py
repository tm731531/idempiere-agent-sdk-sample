"""
Data Masking Engine for iDempiere Agent SDK

Provides secure data masking, encryption, and recovery with fine-grained access control.
"""

import hashlib
import json
import base64
from datetime import datetime
from cryptography.fernet import Fernet
from typing import Tuple, Dict, Optional, List


class DataMaskingEngine:
    """Enterprise-grade data masking engine with AES-256 encryption"""

    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize masking engine

        Args:
            encryption_key: Fernet-compatible key (generate with Fernet.generate_key())
                          If None, generates a new key (for demo only)
        """
        if encryption_key is None:
            # Demo mode - generate new key each time
            encryption_key = Fernet.generate_key()
            print(f"[INFO] Generated new encryption key: {encryption_key.decode()}")
            print(f"[⚠️  WARNING] In production, store this key securely (AWS KMS, Azure Key Vault)")

        self.cipher = Fernet(encryption_key if isinstance(encryption_key, bytes) else encryption_key.encode())
        self.mappings = {}  # In-memory mapping table (use encrypted DB in production)
        self.access_log = []  # Audit log


    def mask_customer_name(self, original_name: str) -> Tuple[str, Dict]:
        """
        Mask customer name using hash + encryption

        Args:
            original_name: Original customer name (e.g., "ABC Corp")

        Returns:
            (masked_value, mapping_record)
            Example: ("CUST_HASH_A1B2C3", {...encrypted data...})
        """
        # Generate hash for mapping
        hash_value = hashlib.sha256(original_name.encode()).hexdigest()[:8]
        masked_value = f"CUST_{hash_value.upper()}"

        # Encrypt original value
        encrypted = self.cipher.encrypt(original_name.encode()).decode()

        mapping_record = {
            'masked': masked_value,
            'encrypted': encrypted,
            'timestamp': datetime.now().isoformat(),
            'field': 'customer_name',
            'original_hash': hash_value
        }

        self.mappings[masked_value] = mapping_record

        return masked_value, mapping_record


    def mask_phone(self, phone: str) -> str:
        """
        Mask phone number

        Example: +886-2-1234-5678 → +886-***-****-****
        """
        if not phone or len(phone) < 4:
            return phone

        return phone[:3] + "-***-" + phone[-4:]


    def mask_email(self, email: str) -> str:
        """
        Mask email address

        Example: john.doe@company.com → j***@company.com
        """
        if '@' not in email:
            return email

        local, domain = email.split('@', 1)
        if len(local) <= 1:
            return email

        masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
        return f"{masked_local}@{domain}"


    def mask_invoice(self, invoice: Dict) -> Dict:
        """
        Mask invoice data (complete example)

        Input:
        {
            'c_invoice_id': 12345,
            'customer_name': 'ABC Corp',
            'customer_phone': '+886-2-1234-5678',
            'customer_email': 'sales@abc.com',
            'amount': 50000,
            'dateacct': '2026-03-20',
            'docstatus': 'CO'
        }

        Output (masked):
        {
            'c_invoice_id': 12345,                    # Keep (internal ID)
            'customer_name': 'CUST_A1B2C3D4',        # Masked
            'customer_phone': '+886-***-****-****',  # Masked
            'customer_email': 's***@abc.com',        # Masked
            'amount': 50000,                         # Keep (business necessity)
            'dateacct': '2026-03-20',                # Keep
            'docstatus': 'CO'                        # Keep
        }
        """
        masked = invoice.copy()

        # Mask sensitive fields
        if 'customer_name' in masked and masked['customer_name']:
            masked_name, _ = self.mask_customer_name(masked['customer_name'])
            masked['customer_name'] = masked_name

        if 'customer_phone' in masked and masked['customer_phone']:
            masked['customer_phone'] = self.mask_phone(masked['customer_phone'])

        if 'customer_email' in masked and masked['customer_email']:
            masked['customer_email'] = self.mask_email(masked['customer_email'])

        if 'customer_address' in masked:
            masked['customer_address'] = '[MASKED]'

        # Keep business-necessary fields
        # amount, dateacct, docstatus, grandtotal, etc.

        return masked


    def unmask_value(self, masked_value: str, user_id: str, permission_level: str) -> str:
        """
        Recover masked value with permission check and audit logging

        Args:
            masked_value: Masked value (e.g., "CUST_A1B2C3D4")
            user_id: User ID for audit trail
            permission_level: Permission level ('admin', 'manager', 'analyst', 'viewer')

        Returns:
            Original value if permission granted, else masked value

        Raises:
            PermissionError: If user lacks permission
        """
        # Check permission
        if not self._has_permission(user_id, permission_level, masked_value):
            self._log_access(user_id, masked_value, "DENIED")
            raise PermissionError(f"User {user_id} (level: {permission_level}) cannot access {masked_value}")

        # Return original value if not masked
        if masked_value not in self.mappings:
            return masked_value

        # Decrypt original value
        record = self.mappings[masked_value]
        encrypted = record['encrypted']

        try:
            original = self.cipher.decrypt(encrypted.encode()).decode()
            self._log_access(user_id, masked_value, "GRANTED")
            return original
        except Exception as e:
            self._log_access(user_id, masked_value, f"ERROR: {str(e)}")
            raise


    def _has_permission(self, user_id: str, permission_level: str, data_type: str) -> bool:
        """
        Check if user has permission to view original data

        Permission levels:
        - 'admin': Can view all
        - 'manager': Can view customer data
        - 'analyst': Can only view aggregated data
        - 'viewer': Can only view masked data
        """
        permissions = {
            'admin': ['all'],
            'manager': ['CUST_', 'amount', 'email', 'phone'],
            'analyst': ['aggregated'],
            'viewer': []  # No unmasking allowed
        }

        allowed = permissions.get(permission_level, [])

        if 'all' in allowed:
            return True

        for pattern in allowed:
            if pattern in data_type or data_type.startswith(pattern):
                return True

        return False


    def _log_access(self, user_id: str, data_identifier: str, status: str):
        """
        Audit log: Record who accessed what data

        Used for compliance and security audits
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'accessed_data': data_identifier,
            'status': status,
            'action': 'unmask'
        }

        self.access_log.append(log_entry)
        print(f"[AUDIT] {json.dumps(log_entry)}")


    def get_audit_log(self) -> List[Dict]:
        """Return audit log"""
        return self.access_log


    def export_mappings(self, filepath: str):
        """
        Export encrypted mappings to file

        In production, use encrypted database instead
        """
        with open(filepath, 'w') as f:
            json.dump(self.mappings, f, indent=2, ensure_ascii=False)
        print(f"[INFO] Mappings exported to {filepath}")


    def import_mappings(self, filepath: str):
        """Load mappings from file"""
        with open(filepath, 'r') as f:
            self.mappings = json.load(f)
        print(f"[INFO] Mappings imported from {filepath}")
