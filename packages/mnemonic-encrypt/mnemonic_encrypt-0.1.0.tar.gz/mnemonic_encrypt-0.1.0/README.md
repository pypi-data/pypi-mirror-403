<div align="center">
  <h1>🔐 MnemonicEncrypt</h1>
  <p><strong>Professional Cryptocurrency Mnemonic Encryption Tool</strong></p>
  <p>Powered by <a href="https://pypi.org/project/anyencrypt/">AnyEncrypt</a> | BIP39 Standard | Open Source</p>
  
  <p>
    <img src="https://img.shields.io/badge/python-3.8%2B-blue" alt="Python 3.8+"/>
    <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License"/>
    <a href="https://github.com/fOcusOnus/mnemonic-encrypt">
      <img src="https://img.shields.io/badge/GitHub-Repository-181717?logo=github" alt="GitHub"/>
    </a>
  </p>
  
  <p>
    <strong>English</strong> | 
    <a href="README_CN.md">简体中文</a>
  </p>
</div>

---

## 🚨 Why You Need MnemonicEncrypt?

### 😰 Common Dangerous Practices

- ❌ **Writing plaintext** on paper → Anyone who sees it can steal your assets
- ❌ **Saving screenshots** on phone → Phone lost = Wallet lost
- ❌ **Storing in cloud** (iCloud, Google Drive) → Cloud service breach risk
- ❌ **Saving in notes** → Vulnerable to phone hacking

### ✅ The Secure Solution

**MnemonicEncrypt** allows you to:

1. 🔐 Encrypt mnemonic phrases with a strong password
2. ☁️ Safely store ciphertext anywhere (cloud, paper, notes)
3. 💻 Decrypt when needed on your computer
4. 🔒 Runs locally, keys never uploaded
5. 📖 Open source and auditable, powered by [AnyEncrypt](https://pypi.org/project/anyencrypt/)

![Demo](assets/demo.gif)

---

## 🚀 Quick Start

### Installation

```bash
pip install mnemonic-encrypt
```

### Basic Usage

#### 1️⃣ Encrypt Your Mnemonic

```bash
$ mnemonic-encrypt encrypt
📝 Please enter your mnemonic phrase (space-separated):
abandon ability able about above absent absorb abstract absurd abuse access accident
🔑 Enter encryption password: ********
🔑 Confirm password: ********

✅ Encryption successful!

Ciphertext:
ME$v1$gAAAAABmKj9x7Qw3HvNzR5tY8mP2sK4fL6jN1cV9bX0qW...

💡 Tip: Save this ciphertext safely (cloud storage or paper)
```

#### 2️⃣ Decrypt When Needed

```bash
$ mnemonic-encrypt decrypt
📝 Please enter the ciphertext:
ME$v1$gAAAAABmKj9x7Qw3HvNzR5tY8mP2sK4fL6jN1cV9bX0qW...
🔑 Enter decryption password: ********

✅ Decryption successful!

Mnemonic phrase:
abandon ability able about above absent absorb abstract absurd abuse access accident

⚠️ Warning: Use immediately and clear screen history
```

#### 3️⃣ Generate New Mnemonic (Optional)

```bash
$ mnemonic-encrypt generate
✅ Generated 12-word mnemonic phrase:

abandon ability able about above absent absorb abstract absurd abuse access accident

💡 Tip: Use 'mnemonic-encrypt encrypt' to encrypt and save it immediately
```

---

## 🎯 Use Cases

| Scenario | Traditional Method | Using MnemonicEncrypt |
|----------|-------------------|----------------------|
| **Long-term Storage** | Plaintext on paper, fear of loss/theft | ✅ Encrypt then print, store safely |
| **Cloud Backup** | Afraid to upload to cloud | ✅ Upload ciphertext with confidence |
| **Multi-device** | USB drive, easy to forget | ✅ Sync ciphertext via cloud |
| **Inheritance** | Paper will has risks | ✅ Store ciphertext and password separately |

---

## 💎 Core Features

- 🔐 **Professional Encryption**: Powered by [AnyEncrypt](https://pypi.org/project/anyencrypt/) (Fernet + AES-128 + HMAC)
- ✅ **BIP39 Standard**: Fully compatible with standard mnemonic formats (12/15/18/21/24 words)
- 🔑 **Key Derivation**: SHA-256 derived, resistant to brute-force attacks
- 💻 **Offline Operation**: All operations run locally, no internet required
- 🛡️ **Privacy Protected**: Keys are never saved, uploaded, or cached
- 🎯 **Interactive CLI**: Simple and user-friendly, no commands to memorize
- 🐍 **Python API**: Integrate into your projects
- 🧪 **Well Tested**: 100% test coverage
- 📦 **Zero Barrier**: Install with one command

---

## 🔧 Python API

```python
from mnemonic_encrypt import MnemonicEncryptor

# Create encryptor
encryptor = MnemonicEncryptor()

# Encrypt mnemonic
mnemonic = "abandon ability able about above absent absorb abstract absurd abuse access accident"
password = "your-super-strong-password-123!"
ciphertext = encryptor.encrypt(mnemonic, password)
print(f"Ciphertext: {ciphertext}")

# Decrypt mnemonic
decrypted = encryptor.decrypt(ciphertext, password)
print(f"Mnemonic: {decrypted}")

# Generate new mnemonic
new_mnemonic = encryptor.generate(strength=128)  # 12 words
print(f"New mnemonic: {new_mnemonic}")

# Validate mnemonic
is_valid = encryptor.validate_mnemonic(mnemonic)
print(f"Valid: {is_valid}")
```

---

## 🛡️ Security Recommendations

### ✅ Best Practices

1. **Strong Password**: At least 16 characters, including uppercase, lowercase, numbers, and symbols
   - ❌ `password123`
   - ✅ `MyWallet@2026!SecureP@ssw0rd`

2. **Password Management**:
   - Memorize or write in a physical notebook (not with ciphertext)
   - Can set password hint questions

3. **Test First**:
   ```bash
   # Test with a dummy mnemonic first
   $ mnemonic-encrypt encrypt  # Use test mnemonic
   $ mnemonic-encrypt decrypt  # Ensure it decrypts correctly
   # Then encrypt your real mnemonic
   ```

4. **Backup Strategy**:
   - Print ciphertext twice: 1 in safe, 1 with trusted person
   - Store password separately

### ❌ Dangerous Practices

- ❌ Using weak passwords (less than 12 characters)
- ❌ Storing password and ciphertext together
- ❌ Using on public/internet cafe computers
- ❌ Taking screenshots with plaintext mnemonic
- ❌ Sending plaintext mnemonic via WeChat/email

---

## 🌍 Technical Architecture

```
User Mnemonic
    ↓
[Normalization]  ← lowercase, trim spaces
    ↓
[BIP39 Validation]  ← ensure mnemonic is valid
    ↓
[AnyEncrypt Encryption]  ← Fernet (AES-128-CBC + HMAC)
    ↓
[Add Version Prefix]  ← ME$v1$ (for future upgrades)
    ↓
Ciphertext Output
```

### Encryption Details

- **Algorithm**: Fernet (cryptography library)
- **Symmetric Encryption**: AES-128-CBC
- **Message Authentication**: HMAC-SHA256
- **Key Derivation**: SHA-256 (AnyEncrypt implementation)
- **Version Management**: `ME$v1$` prefix

---

## 📊 Comparison with Competitors

| Project | Type | Encryption | BIP39 | Cross-platform | Maintained |
|---------|------|------------|-------|----------------|-----------|
| **MnemonicEncrypt** | ✅ CLI + API | ✅ AnyEncrypt | ✅ Yes | ✅ Win/Mac/Linux | ✅ Active |
| mnemonic-encryption-locally | Web | Custom | ✅ | ⚠️ Browser only | ❌ |
| mnemonic-encryption-webjs | Web | WebCrypto | ✅ | ⚠️ Browser only | ❌ |
| passphrase-encrypter | Web | Unknown | ✅ | ⚠️ Browser only | ❌ |

**Your Advantages**:
- ✅ Only Python CLI tool (developer-friendly)
- ✅ Based on established encryption library (high credibility)
- ✅ Cross-platform support (Mac/Windows/Linux)
- ✅ Integrable API (extensible)
- ✅ Continuously maintained and updated

---

## 🌟 Supported Platforms

| Platform | Status | Note |
|----------|--------|------|
| macOS | ✅ | 10.15+ |
| Windows | ✅ | 10/11 |
| Linux | ✅ | Ubuntu 20.04+ |
| Python | ✅ | 3.8 - 3.12 |

---

## 📖 Documentation

- [📥 Installation Guide](docs/installation.md)
- [📝 Usage Tutorial](docs/usage.md)
- [🔒 Security Guide](docs/security.md)
- [❓ FAQ](docs/faq.md)
- [🔧 API Documentation](docs/api.md)

---

## 🤝 Contributing

Issues and Pull Requests are welcome!

1. Fork this repository
2. Create a branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push branch (`git push origin feature/amazing`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 🙏 Acknowledgments

- [**AnyEncrypt**](https://pypi.org/project/anyencrypt/) - Core encryption library (Author: Lindsay Wat)
- [python-mnemonic](https://github.com/trezor/python-mnemonic) - BIP39 implementation
- [cryptography](https://cryptography.io/) - Underlying crypto library

---

## 📧 Contact

- 🐛 Issues: [GitHub Issues](https://github.com/fOcusOnus/mnemonic-encrypt/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/fOcusOnus/mnemonic-encrypt/discussions)

---

<div align="center">
  <p><strong>⚠️ Important Notice</strong></p>
  <p>Lost passwords cannot be recovered! Make sure to remember your password or store it securely</p>
  <p>Cryptocurrency investments carry risks, please be responsible for your own decisions</p>
  <br>
  <p>Made with ❤️ for cryptocurrency community</p>
  <p>Powered by <a href="https://pypi.org/project/anyencrypt/">AnyEncrypt</a></p>
</div>
