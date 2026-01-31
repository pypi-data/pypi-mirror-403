# AnyEncrypt

A simple and easy-to-use command-line encryption/decryption tool. Supports encrypting and decrypting both text and files.

## Features

- 🔐 Strong encryption (Fernet - symmetric encryption)
- 🔑 Custom passwords supported
- 📝 Text encryption/decryption
- 📁 File encryption/decryption
- 🎯 Simple CLI interface
- 🔒 Passwords are hidden from shell history

## Installation

### Install from PyPI (recommended)

```bash
pip install anyencrypt
```

### Install from source

```bash
cd anyencrypt
pip install -e .
```

## Usage

### Interactive Mode (recommended)

The easiest way to use it! Just run `anyencrypt` and follow the prompts:

```bash
anyencrypt
```

You will be asked:
1. Choose encrypt or decrypt
2. Choose text or file
3. Enter password
4. Enter the content to process

### Command Line Mode

If you prefer CLI arguments, use:

#### Encrypt text

```bash
# Enter password interactively (recommended)
anyencrypt encrypt -t "Hello World"

# Or specify password directly (not recommended, stored in history)
anyencrypt encrypt -t "Hello World" -p yourpassword
```

#### Decrypt text

```bash
anyencrypt decrypt -t "gAAAAAB..."
```

#### Encrypt file

```bash
# Encrypt file, output name generated automatically
anyencrypt encrypt -f secret.txt

# Or specify output file name
anyencrypt encrypt -f secret.txt -o secret.encrypted
```

#### Decrypt file

```bash
# Decrypt file, output name generated automatically
anyencrypt decrypt -f secret.encrypted

# Or specify output file name
anyencrypt decrypt -f secret.encrypted -o secret.txt
```

### Help

```bash
anyencrypt --help
anyencrypt encrypt --help
anyencrypt decrypt --help
```

## Python API

You can also use AnyEncrypt in Python code:

```python
from anyencrypt import encrypt_text, decrypt_text, encrypt_file, decrypt_file

# Encrypt text
encrypted = encrypt_text("Hello World", "your-password")
print(encrypted)

# Decrypt text
decrypted = decrypt_text(encrypted, "your-password")
print(decrypted)

# Encrypt file
encrypt_file("input.txt", "output.encrypted", "your-password")

# Decrypt file
decrypt_file("output.encrypted", "decrypted.txt", "your-password")
```

## Security Tips

1. **Do not enter passwords directly in the command line** (using `-p`), as it will be saved in shell history
2. **Use strong passwords** - at least 12 characters recommended
3. **Keep passwords safe** - lost passwords cannot be recovered
4. **Backup important data** - back up files before encrypting

## Technical Details

- Uses Fernet from `cryptography` (symmetric encryption)
- Derives keys from passwords using SHA-256
- Uses AES-128 (CBC mode)
- Uses HMAC for authentication

## Dependencies

- Python >= 3.8
- cryptography >= 41.0.0
- click >= 8.0.0

## Development

```bash
cd anyencrypt

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .

# Lint
flake8
```

## License

MIT License - see [LICENSE](LICENSE)

## Author

Lindsay Wat - llindsaywat1985@gmail.com

## Contributing

Issues and pull requests are welcome!

## Changelog

### 0.2.0 (2026-01-29)

- ✨ Added interactive mode - just run `anyencrypt` to start
- 🎯 Guides users through encryption/decryption
- 💡 Improved user experience
- 📝 Keeps the original CLI argument mode

### 0.1.0 (2026-01-29)

- Initial release
- Supports text and file encryption/decryption
- Command line interface
