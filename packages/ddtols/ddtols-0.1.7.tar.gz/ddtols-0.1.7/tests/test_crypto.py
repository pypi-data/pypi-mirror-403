import pytest

from ddtols import AESCipher, RSACipher, init

@pytest.fixture(autouse=True)
def setup_module():
    # 确保初始化
    init()

def test_aes_cipher():
    # 1. 生成密钥
    key_b64 = AESCipher.generate_key()
    assert len(key_b64) > 0
    
    # 2. 初始化
    cipher = AESCipher(key_b64)
    
    # 3. 加密
    plaintext = "Hello, World! This is a secret."
    encrypted = cipher.encrypt(plaintext)
    assert encrypted != plaintext
    
    # 4. 解密
    decrypted = cipher.decrypt(encrypted)
    assert decrypted == plaintext
    
    # 5. 测试不同数据类型 (bytes)
    data_bytes = b"Binary data"
    encrypted_bytes = cipher.encrypt(data_bytes)
    decrypted_bytes = cipher.decrypt(encrypted_bytes)
    # decrypt 返回的是 str (utf-8 decoded)，所以要 encode 对比，或者我们设计的 decrypt 总是返回 str
    # 我们的设计是 decrypt 返回 str，所以输入必须是 utf-8 兼容的
    # 如果要支持任意二进制，decrypt 可能需要改。但在本库中暂时假设是文本。
    assert decrypted_bytes == "Binary data"

def test_aes_invalid_key():
    with pytest.raises(ValueError, match="Invalid key length"):
        AESCipher(b"short")

def test_aes_decryption_failure():
    key1 = AESCipher.generate_key()
    key2 = AESCipher.generate_key()
    
    cipher1 = AESCipher(key1)
    cipher2 = AESCipher(key2)
    
    plaintext = "Sensitive Data"
    encrypted = cipher1.encrypt(plaintext)
    
    # 用错误的密钥解密
    with pytest.raises(ValueError, match="Decryption failed"):
        cipher2.decrypt(encrypted)

def test_rsa_cipher():
    # 1. 生成密钥对
    priv_pem, pub_pem = RSACipher.generate_keys()
    assert "BEGIN PRIVATE KEY" in priv_pem
    assert "BEGIN PUBLIC KEY" in pub_pem
    
    # 2. 初始化 (全功能)
    cipher = RSACipher(private_key_pem=priv_pem, public_key_pem=pub_pem)
    
    # 3. 加密
    plaintext = "RSA is cool"
    encrypted = cipher.encrypt(plaintext)
    
    # 4. 解密
    decrypted = cipher.decrypt(encrypted)
    assert decrypted == plaintext

def test_rsa_public_only():
    """测试只有公钥的情况（只能加密）"""
    _, pub_pem = RSACipher.generate_keys()
    cipher = RSACipher(public_key_pem=pub_pem)
    
    encrypted = cipher.encrypt("Hello")
    
    # 无法解密
    with pytest.raises(ValueError, match="Private key is required"):
        cipher.decrypt(encrypted)

def test_rsa_private_only():
    """测试只有私钥的情况（可以推导出公钥，应该能加解密）"""
    priv_pem, _ = RSACipher.generate_keys()
    cipher = RSACipher(private_key_pem=priv_pem)
    
    # 加密（应该成功，因为有了私钥就有了公钥）
    # 实际上 RSACipher 的 __init__ 中我们做了 self.public_key = self.private_key.public_key()
    encrypted = cipher.encrypt("Hello")
    decrypted = cipher.decrypt(encrypted)
    assert decrypted == "Hello"
