import base64
import logging
from typing import Union, Optional
import boto3
from botocore.exceptions import ClientError
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os
import json

logger = logging.getLogger(__name__)

class EncryptionManager:
    """Production-grade encryption manager for healthcare data"""[1]
    
    def __init__(self):
        self.kms_client = boto3.client('kms')
        self.kms_key_id = os.environ.get('KMS_KEY_ID')
        self._fernet_key = None
    
    def encrypt_with_kms(self, plaintext: Union[str, bytes], encryption_context: Optional[dict] = None) -> str:
        """Encrypt data using AWS KMS"""[1]
        try:
            if isinstance(plaintext, str):
                plaintext = plaintext.encode('utf-8')
            
            kwargs = {
                'KeyId': self.kms_key_id,
                'Plaintext': plaintext
            }
            
            if encryption_context:
                kwargs['EncryptionContext'] = encryption_context
            
            response = self.kms_client.encrypt(**kwargs)
            
            # Return base64 encoded ciphertext
            ciphertext_blob = response['CiphertextBlob']
            return base64.b64encode(ciphertext_blob).decode('utf-8')
            
        except ClientError as e:
            logger.error(f"KMS encryption failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Encryption error: {str(e)}")
            raise
    
    def decrypt_with_kms(self, ciphertext: str, encryption_context: Optional[dict] = None) -> str:
        """Decrypt data using AWS KMS"""[1]
        try:
            # Decode base64 ciphertext
            ciphertext_blob = base64.b64decode(ciphertext.encode('utf-8'))
            
            kwargs = {
                'CiphertextBlob': ciphertext_blob
            }
            
            if encryption_context:
                kwargs['EncryptionContext'] = encryption_context
            
            response = self.kms_client.decrypt(**kwargs)
            
            return response['Plaintext'].decode('utf-8')
            
        except ClientError as e:
            logger.error(f"KMS decryption failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Decryption error: {str(e)}")
            raise
    
    def encrypt_pii_data(self, data: dict, patient_id: str) -> dict:
        """Encrypt PII data with patient-specific context"""[1]
        try:
            encryption_context = {
                'patient_id': patient_id,
                'data_type': 'pii'
            }
            
            encrypted_data = {}
            
            # Fields that should be encrypted
            pii_fields = [
                'name', 'email', 'phone', 'address', 'ssn', 
                'date_of_birth', 'emergency_contact'
            ]
            
            for key, value in data.items():
                if key in pii_fields and value:
                    if isinstance(value, dict):
                        # Encrypt nested objects
                        encrypted_data[key] = self.encrypt_pii_data(value, patient_id)
                    else:
                        # Encrypt the value
                        encrypted_value = self.encrypt_with_kms(
                            json.dumps(value) if not isinstance(value, str) else value,
                            encryption_context
                        )
                        encrypted_data[key] = {
                            'encrypted': True,
                            'value': encrypted_value
                        }
                else:
                    # Keep non-PII data as is
                    encrypted_data[key] = value
            
            return encrypted_data
            
        except Exception as e:
            logger.error(f"Error encrypting PII data: {str(e)}")
            raise
    
    def decrypt_pii_data(self, encrypted_data: dict, patient_id: str) -> dict:
        """Decrypt PII data with patient-specific context"""[1]
        try:
            encryption_context = {
                'patient_id': patient_id,
                'data_type': 'pii'
            }
            
            decrypted_data = {}
            
            for key, value in encrypted_data.items():
                if isinstance(value, dict) and value.get('encrypted'):
                    # Decrypt the value
                    decrypted_value = self.decrypt_with_kms(
                        value['value'],
                        encryption_context
                    )
                    
                    # Try to parse as JSON, fallback to string
                    try:
                        decrypted_data[key] = json.loads(decrypted_value)
                    except json.JSONDecodeError:
                        decrypted_data[key] = decrypted_value
                        
                elif isinstance(value, dict) and not value.get('encrypted'):
                    # Recursively decrypt nested objects
                    decrypted_data[key] = self.decrypt_pii_data(value, patient_id)
                else:
                    # Keep non-encrypted data as is
                    decrypted_data[key] = value
            
            return decrypted_data
            
        except Exception as e:
            logger.error(f"Error decrypting PII data: {str(e)}")
            raise
    
    def generate_data_key(self, key_spec: str = 'AES_256') -> dict:
        """Generate data key for envelope encryption"""[1]
        try:
            response = self.kms_client.generate_data_key(
                KeyId=self.kms_key_id,
                KeySpec=key_spec
            )
            
            return {
                'plaintext_key': response['Plaintext'],
                'encrypted_key': base64.b64encode(response['CiphertextBlob']).decode('utf-8')
            }
            
        except ClientError as e:
            logger.error(f"Data key generation failed: {str(e)}")
            raise
    
    def get_fernet_key(self, password: Optional[str] = None) -> Fernet:
        """Get Fernet encryption key for local encryption"""[1]
        if self._fernet_key is None:
            if password is None:
                password = os.environ.get('ENCRYPTION_PASSWORD', 'default_password')
            
            # Derive key from password
            password_bytes = password.encode()
            salt = b'healthconnect_salt'  # In production, use random salt
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            
            key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
            self._fernet_key = Fernet(key)
        
        return self._fernet_key
    
    def encrypt_local(self, data: Union[str, bytes]) -> str:
        """Encrypt data locally using Fernet"""[1]
        try:
            fernet = self.get_fernet_key()
            
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            encrypted_data = fernet.encrypt(data)
            return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Local encryption failed: {str(e)}")
            raise
    
    def decrypt_local(self, encrypted_data: str) -> str:
        """Decrypt data locally using Fernet"""[1]
        try:
            fernet = self.get_fernet_key()
            
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            decrypted_data = fernet.decrypt(encrypted_bytes)
            
            return decrypted_data.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Local decryption failed: {str(e)}")
            raise
    
    def hash_sensitive_data(self, data: str, salt: Optional[str] = None) -> str:
        """Hash sensitive data for indexing/searching"""[1]
        try:
            import hashlib
            
            if salt is None:
                salt = os.environ.get('HASH_SALT', 'healthconnect_hash_salt')
            
            # Combine data with salt
            salted_data = f"{data}{salt}".encode('utf-8')
            
            # Create SHA-256 hash
            hash_object = hashlib.sha256(salted_data)
            return hash_object.hexdigest()
            
        except Exception as e:
            logger.error(f"Hashing failed: {str(e)}")
            raise

# Global instance
encryption_manager = EncryptionManager()
