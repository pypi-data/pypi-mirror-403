# AnyEncrypt

[English](README.en.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Français](README.fr.md) | 简体中文

一个简单易用的命令行加密解密工具，支持文本和文件的加密解密操作。

## 特性

- 🔐 使用强加密算法（Fernet - 对称加密）
- 🔑 支持自定义密码
- 📝 支持文本加密/解密
- 📁 支持文件加密/解密
- 🎯 简单易用的命令行接口
- 🔒 密码不会显示在命令历史中

## 安装

### 从 PyPI 安装（推荐）

```bash
pip install anyencrypt
```

### 从源码安装

```bash
cd anyencrypt
pip install -e .
```

## 使用方法

### 交互式模式（推荐）

最简单的使用方式！只需输入 `anyencrypt`，程序会引导你完成所有操作：

```bash
anyencrypt
```

程序会依次询问：
1. 选择加密还是解密
2. 选择处理文本还是文件
3. 输入密码
4. 输入要处理的内容

### 命令行模式

如果你更喜欢命令行参数，也可以使用以下方式：

#### 加密文本

```bash
# 交互式输入密码（推荐）
anyencrypt encrypt -t "Hello World"

# 或直接指定密码（不推荐，会在命令历史中留下记录）
anyencrypt encrypt -t "Hello World" -p yourpassword
```

#### 解密文本

```bash
anyencrypt decrypt -t "gAAAAAB..."
```

#### 加密文件

```bash
# 加密文件，自动生成输出文件名
anyencrypt encrypt -f secret.txt

# 或指定输出文件名
anyencrypt encrypt -f secret.txt -o secret.encrypted
```

#### 解密文件

```bash
# 解密文件，自动生成输出文件名
anyencrypt decrypt -f secret.encrypted

# 或指定输出文件名
anyencrypt decrypt -f secret.encrypted -o secret.txt
```

### 查看帮助

```bash
anyencrypt --help
anyencrypt encrypt --help
anyencrypt decrypt --help
```

## Python API

除了命令行工具，你也可以在 Python 代码中使用：

```python
from anyencrypt import encrypt_text, decrypt_text, encrypt_file, decrypt_file

# 加密文本
encrypted = encrypt_text("Hello World", "your-password")
print(encrypted)

# 解密文本
decrypted = decrypt_text(encrypted, "your-password")
print(decrypted)

# 加密文件
encrypt_file("input.txt", "output.encrypted", "your-password")

# 解密文件
decrypt_file("output.encrypted", "decrypted.txt", "your-password")
```

## 安全提示

1. **不要在命令行中直接输入密码**（使用 `-p` 参数），这会将密码保存在命令历史中
2. **使用强密码** - 建议使用至少 12 位的复杂密码
3. **妥善保管密码** - 密码丢失后无法恢复加密的数据
4. **备份重要数据** - 加密前请备份原始文件

## 技术细节

- 使用 `cryptography` 库的 Fernet 实现（对称加密）
- 使用 SHA-256 从密码派生密钥
- 使用 AES-128 加密算法（CBC 模式）
- 使用 HMAC 进行消息认证

## 依赖

- Python >= 3.8
- cryptography >= 41.0.0
- click >= 8.0.0

## 开发

```bash
cd anyencrypt

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
black .

# 代码检查
flake8
```

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 作者

Lindsay Wat - llindsaywat1985@gmail.com

## 贡献

欢迎提交 Issue 和 Pull Request！

## 更新日志

### 0.2.0 (2026-01-29)

- ✨ 新增交互式模式 - 只需输入 `anyencrypt` 即可开始使用
- 🎯 智能引导用户完成加密/解密操作
- 💡 更友好的用户体验
- 📝 保留原有命令行参数模式

### 0.1.0 (2026-01-29)

- 初始版本
- 支持文本和文件的加密解密
- 命令行接口
- Python API
