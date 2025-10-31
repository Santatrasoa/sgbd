# utils/crypto.py
from cryptography.fernet import Fernet, InvalidToken
import hashlib
import base64
import json

class CryptoManager:
    def __init__(self, password: str):
        self.key = self._derive_key(password)
        self.fernet = Fernet(self.key)

    def _derive_key(self, password: str) -> bytes:
        salt = b'my_sgbd_secure_salt_2025'
        # CORRIGÉ : pbkdf2_hmac (pas pリティ2_hmac !)
        kdf = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 200000)
        return base64.urlsafe_b64encode(kdf)

    def encrypt(self, data: dict) -> bytes:
        json_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        return self.fernet.encrypt(json_str.encode('utf-8'))

    def decrypt(self, encrypted: bytes) -> dict:
        try:
            decrypted = self.fernet.decrypt(encrypted).decode('utf-8')
            return json.loads(decrypted)
        except InvalidToken:
            print("Error: Wrong password or corrupted file")
            exit(1)