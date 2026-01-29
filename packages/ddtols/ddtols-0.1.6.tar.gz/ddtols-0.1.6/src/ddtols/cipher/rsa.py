from __future__ import annotations

import base64
from typing import cast

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding, rsa

from ..decorators import log_execution
from ..diary import get_logger

logger = get_logger("cipher.rsa")

class RSACipher:
    """
    RSA 加解密工具类。
    
    支持生成密钥对、公钥加密、私钥解密。
    """
    
    @log_execution
    def __init__(
        self,
        private_key_pem: str | bytes | None = None,
        public_key_pem: str | bytes | None = None,
    ):
        """
        初始化 RSACipher。
        
        可以传入私钥、公钥或两者都传。
        如果要解密，必须传私钥。
        如果要加密，必须传公钥（如果传了私钥，会自动推导出公钥）。
        """
        self.private_key: rsa.RSAPrivateKey | None = None
        self.public_key: rsa.RSAPublicKey | None = None
        
        if private_key_pem:
            if isinstance(private_key_pem, str):
                private_key_pem = private_key_pem.encode('utf-8')
            try:
                loaded_private = serialization.load_pem_private_key(
                    private_key_pem,
                    password=None
                )
                self.private_key = cast(rsa.RSAPrivateKey, loaded_private)
                self.public_key = cast(rsa.RSAPublicKey, self.private_key.public_key())
                logger.debug("RSACipher loaded private key")
            except Exception as e:
                logger.exception("Failed to load private key")
                raise ValueError("Invalid private key") from e
                
        if public_key_pem:
            if isinstance(public_key_pem, str):
                public_key_pem = public_key_pem.encode('utf-8')
            try:
                loaded_public = serialization.load_pem_public_key(public_key_pem)
                self.public_key = cast(rsa.RSAPublicKey, loaded_public)
                logger.debug("RSACipher loaded public key")
            except Exception as e:
                logger.exception("Failed to load public key")
                raise ValueError("Invalid public key") from e
                
        if not self.public_key and not self.private_key:
            logger.warning("RSACipher initialized without keys")

    @log_execution
    def encrypt(self, plaintext: str | bytes) -> str:
        """
        使用公钥加密。
        
        返回：
        str: Base64 编码的密文。
        """
        if not self.public_key:
            raise ValueError("Public key is required for encryption")
            
        if isinstance(plaintext, str):
            data = plaintext.encode('utf-8')
        else:
            data = plaintext
            
        try:
            ciphertext = self.public_key.encrypt(
                data,
                asym_padding.OAEP(
                    mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return base64.b64encode(ciphertext).decode('utf-8')
        except Exception:
            logger.exception("RSA Encryption failed")
            raise

    @log_execution
    def decrypt(self, encrypted_data: str) -> str:
        """
        使用私钥解密。
        
        参数：
        encrypted_data (str): Base64 编码的密文。
        
        返回：
        str: 解密后的明文。
        """
        if not self.private_key:
            raise ValueError("Private key is required for decryption")
            
        try:
            ciphertext = base64.b64decode(encrypted_data)
            plaintext = self.private_key.decrypt(
                ciphertext,
                asym_padding.OAEP(
                    mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return plaintext.decode('utf-8')
        except Exception as e:
            logger.exception("RSA Decryption failed")
            raise ValueError("Decryption failed") from e

    @staticmethod
    @log_execution
    def generate_keys(key_size: int = 2048) -> tuple[str, str]:
        """
        生成 RSA 密钥对。
        
        返回：
        (private_key_pem, public_key_pem) 均为 UTF-8 字符串。
        """
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size
        )
        
        priv_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        
        pub_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        
        logger.debug(f"Generated RSA key pair ({key_size} bits)")
        return priv_pem, pub_pem
