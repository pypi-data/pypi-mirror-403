"""
加密解密功能测试
"""

import pytest
import tempfile
from pathlib import Path

from anyencrypt.crypto import (
    encrypt_text,
    decrypt_text,
    encrypt_file,
    decrypt_file,
    _encrypt_for_api,
)


class TestTextEncryption:
    """文本加密解密测试"""
    
    def test_encrypt_decrypt_text(self):
        """测试文本加密和解密"""
        original = "Hello World! 你好世界！"
        password = "test-password-123"
        
        # 加密
        encrypted = encrypt_text(original, password)
        assert encrypted != original
        assert len(encrypted) > 0
        
        # 解密
        decrypted = decrypt_text(encrypted, password)
        assert decrypted == original
    
    def test_wrong_password(self):
        """测试错误密码解密"""
        text = "Secret Message"
        password = "correct-password"
        wrong_password = "wrong-password"
        
        encrypted = encrypt_text(text, password)
        
        with pytest.raises(Exception) as exc_info:
            decrypt_text(encrypted, wrong_password)
        
        # 接受中文或英文错误消息
        error_msg = str(exc_info.value)
        assert "密码错误" in error_msg or "wrong password" in error_msg or "corrupted" in error_msg
    
    def test_empty_text(self):
        """测试空文本加密"""
        password = "test-password"
        
        encrypted = encrypt_text("", password)
        decrypted = decrypt_text(encrypted, password)
        
        assert decrypted == ""
    
    def test_unicode_text(self):
        """测试 Unicode 文本"""
        text = "测试中文 🔐 Emoji 日本語 한국어"
        password = "unicode-test"
        
        encrypted = encrypt_text(text, password)
        decrypted = decrypt_text(encrypted, password)
        
        assert decrypted == text
    
    def test_api_encrypt_compat_ascii(self):
        """测试 API 加密与 JS 版本兼容(ASCII)"""
        content = "test"
        expected = "GRxeBw=="
        
        encrypted = _encrypt_for_api(content)
        assert encrypted == expected


class TestFileEncryption:
    """文件加密解密测试"""
    
    def test_encrypt_decrypt_file(self):
        """测试文件加密和解密"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试文件
            input_file = Path(tmpdir) / "test.txt"
            encrypted_file = Path(tmpdir) / "test.encrypted"
            output_file = Path(tmpdir) / "test_decrypted.txt"
            
            original_content = "This is a test file.\n测试文件内容。"
            input_file.write_text(original_content, encoding='utf-8')
            
            password = "file-password-123"
            
            # 加密文件
            encrypt_file(input_file, encrypted_file, password)
            assert encrypted_file.exists()
            
            # 确认加密后的内容不同
            encrypted_content = encrypted_file.read_bytes()
            assert encrypted_content != original_content.encode('utf-8')
            
            # 解密文件
            decrypt_file(encrypted_file, output_file, password)
            assert output_file.exists()
            
            # 验证解密后的内容
            decrypted_content = output_file.read_text(encoding='utf-8')
            assert decrypted_content == original_content
    
    def test_binary_file_encryption(self):
        """测试二进制文件加密"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建二进制测试文件
            input_file = Path(tmpdir) / "test.bin"
            encrypted_file = Path(tmpdir) / "test.encrypted"
            output_file = Path(tmpdir) / "test_decrypted.bin"
            
            original_data = bytes(range(256))  # 0-255 的字节
            input_file.write_bytes(original_data)
            
            password = "binary-password"
            
            # 加密
            encrypt_file(input_file, encrypted_file, password)
            
            # 解密
            decrypt_file(encrypted_file, output_file, password)
            
            # 验证
            decrypted_data = output_file.read_bytes()
            assert decrypted_data == original_data
    
    def test_file_not_found(self):
        """测试文件不存在的情况"""
        password = "test-password"
        
        with pytest.raises(FileNotFoundError):
            encrypt_file("/nonexistent/file.txt", "/tmp/output.txt", password)
    
    def test_wrong_password_file(self):
        """测试文件解密时使用错误密码"""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "test.txt"
            encrypted_file = Path(tmpdir) / "test.encrypted"
            output_file = Path(tmpdir) / "test_decrypted.txt"
            
            input_file.write_text("Secret content")
            
            correct_password = "correct"
            wrong_password = "wrong"
            
            # 加密
            encrypt_file(input_file, encrypted_file, correct_password)
            
            # 用错误密码解密
            with pytest.raises(Exception) as exc_info:
                decrypt_file(encrypted_file, output_file, wrong_password)
            
            # 接受中文或英文错误消息
            error_msg = str(exc_info.value)
            assert "密码错误" in error_msg or "wrong password" in error_msg or "corrupted" in error_msg


class TestPasswordDerivation:
    """密码派生测试"""
    
    def test_same_password_different_keys(self):
        """测试相同密码在不同时间生成相同的密钥"""
        text = "Test message"
        password = "same-password"
        
        # 多次加密同一文本
        encrypted1 = encrypt_text(text, password)
        encrypted2 = encrypt_text(text, password)
        
        # 虽然加密结果不同（因为有随机 IV）
        # 但都应该能用同一密码解密
        assert decrypt_text(encrypted1, password) == text
        assert decrypt_text(encrypted2, password) == text
    
    def test_different_passwords(self):
        """测试不同密码生成不同的密钥"""
        text = "Test message"
        password1 = "password1"
        password2 = "password2"
        
        encrypted1 = encrypt_text(text, password1)
        encrypted2 = encrypt_text(text, password2)
        
        # 用错误的密码解密应该失败
        with pytest.raises(Exception):
            decrypt_text(encrypted1, password2)
        
        with pytest.raises(Exception):
            decrypt_text(encrypted2, password1)
    
    def test_unicode_and_multibyte_characters(self):
        """测试多语言和多字节字符的加密解密"""
        password = "test123"
        
        test_cases = [
            "中文测试",
            "日本語テスト",
            "Тест на русском",
            "한국어 테스트",
            "مرحبا",
            "🎉 Emoji test! 🚀",
            "Mixed: 中文English日本語123",
            "这是一个包含各种字符的长文本：ABC、123、特殊符号！@#$%^&*()",
        ]
        
        for text in test_cases:
            encrypted = encrypt_text(text, password)
            decrypted = decrypt_text(encrypted, password)
            assert decrypted == text, f"解密失败: {text}"
    
    def test_api_encryption_with_chinese(self):
        """测试中文内容的 API 加密功能"""
        from anyencrypt.crypto import _encrypt_for_api
        
        # 测试中文内容可以正确加密为 Base64
        chinese_text = "测试中文加密"
        result = _encrypt_for_api(chinese_text)
        
        # 验证结果是有效的 Base64 字符串
        assert isinstance(result, str)
        assert len(result) > 0
        
        # 验证可以解码回字节
        import base64
        decoded = base64.b64decode(result)
        assert isinstance(decoded, bytes)
        assert len(decoded) > 0
