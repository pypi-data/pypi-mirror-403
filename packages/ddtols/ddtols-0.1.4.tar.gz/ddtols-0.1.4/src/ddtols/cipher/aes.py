from __future__ import annotations

import base64
import os

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from ..decorators import log_execution
from ..diary import get_logger

logger = get_logger("cipher.aes")

class AESCipher:
    """
    AES 加密工具类。
    
    使用 AES-GCM 模式，提供认证加密，确保数据的机密性和完整性。
    """
    
    @log_execution
    def __init__(self, key: bytes | str):
        """
        初始化 AESCipher。
        
        参数：
        key (bytes | str): 密钥。如果是字符串，必须是 base64 编码的。
                           对于 AES-256，密钥长度必须是 32 字节。
                           对于 AES-128，密钥长度必须是 16 字节。
        """
        if isinstance(key, str):
            try:
                self.key = base64.b64decode(key)
            except Exception as e:
                logger.exception("Invalid base64 key")
                raise ValueError("Key must be valid base64 string or bytes") from e
        else:
            self.key = key
            
        if len(self.key) not in (16, 24, 32):
            err_msg = f"Invalid key length: {len(self.key)}. Must be 16, 24, or 32 bytes."
            logger.error(err_msg)
            raise ValueError(err_msg)
            
        logger.debug(f"AESCipher initialized with key length: {len(self.key)}")

    @log_execution
    def encrypt(self, plaintext: str | bytes) -> str:
        """
        加密数据。
        
        参数：
        plaintext (str | bytes): 待加密的明文。
        
        返回：
        str: 加密后的数据（Base64 编码字符串）。
             格式包含 nonce 和 ciphertext。
        """
        if isinstance(plaintext, str):
            data = plaintext.encode('utf-8')
        else:
            data = plaintext
            
        # 生成随机 Nonce (GCM 推荐 12 字节)
        nonce = os.urandom(12)
        
        # 加密
        cipher = Cipher(algorithms.AES(self.key), modes.GCM(nonce))
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(data) + encryptor.finalize()
        
        # 获取认证标签
        tag = encryptor.tag
        
        # 拼接：nonce + tag + ciphertext
        # 这样解密时可以方便拆分
        combined = nonce + tag + ciphertext
        
        result = base64.b64encode(combined).decode('utf-8')
        logger.debug(f"AES Encrypted data length: {len(result)}")
        return result

    @log_execution
    def decrypt(self, encrypted_data: str) -> str:
        """
        解密数据。
        
        参数：
        encrypted_data (str): 加密后的 Base64 字符串。
        
        返回：
        str: 解密后的明文（UTF-8 字符串）。
        
        异常：
        ValueError: 如果解密失败（如密钥错误或数据被篡改）。
        """
        try:
            combined = base64.b64decode(encrypted_data)
            
            # 拆分
            # GCM nonce: 12 bytes
            # GCM tag: 16 bytes
            if len(combined) < 28:
                raise ValueError("Invalid encrypted data length")
                
            nonce = combined[:12]
            tag = combined[12:28]
            ciphertext = combined[28:]
            
            # 解密
            cipher = Cipher(algorithms.AES(self.key), modes.GCM(nonce, tag))
            decryptor = cipher.decryptor()
            plaintext_bytes = decryptor.update(ciphertext) + decryptor.finalize()
            
            result = plaintext_bytes.decode('utf-8')
            logger.debug("AES Decryption successful")
            return result
            
        except Exception as e:
            logger.exception("AES Decryption failed")
            raise ValueError("Decryption failed. Data may be corrupted or key is incorrect.") from e

    @staticmethod
    @log_execution
    def generate_key(key_size: int = 32) -> str:
        """
        生成一个随机的 AES 密钥（Base64 编码）。
        
        参数：
        key_size (int): 密钥长度（字节），默认 32 (AES-256)。
        
        返回：
        str: Base64 编码的密钥。
        """
        key = os.urandom(key_size)
        return base64.b64encode(key).decode('utf-8')
