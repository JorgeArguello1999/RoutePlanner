from cryptography.fernet import Fernet
from config import Config
import json

class Encryption:
    def __init__(self):
        self.key = Config.ENCRYPTION_KEY
        if not self.key:
           raise ValueError("ENCRYPTION_KEY must be set in environment variables.")
        self.cipher_suite = Fernet(self.key)

    def encrypt_value(self, value):
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        return self.cipher_suite.encrypt(value.encode()).decode()

    def decrypt_value(self, value):
        if value is None:
            return None
        decrypted_data = self.cipher_suite.decrypt(value.encode()).decode()
        try:
            return json.loads(decrypted_data)
        except json.JSONDecodeError:
            return decrypted_data
