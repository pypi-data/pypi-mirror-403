# Quantum Hydra Cipher v3.0

A powerful 7-layer encryption system that supports multiple file formats including text, PDF, images, videos, and audio files.

## Features

- **7-Layer Military-Grade Encryption**
  1. Salted Key Derivation (PBKDF2 with 150,000 iterations)
  2. Polyalphabetic Vigenère with Dynamic Alphabet Rotation (text only)
  3. Prime-Based Columnar Transposition
  4. SHA-512 XOR Stream Cipher
  5. 256-Byte S-Box Substitution
  6. 8-Round Feistel Network
  7. HMAC-SHA256 + CRC32 Integrity Verification

- **Multi-Format Support**
  - Text: `.txt`
  - Documents: `.pdf`
  - Images: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.webp`, `.tiff`
  - Videos: `.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`, `.flv`, `.wmv`
  - Audio: `.mp3`, `.wav`, `.flac`, `.aac`, `.ogg`, `.m4a`, `.wma`

- **Security Features**
  - Auto-delete original files after encryption
  - Auto-delete encrypted files after decryption
  - Timestamp tracking for all operations
  - Integrity verification with HMAC and CRC32
  - Password-based encryption with key stretching

## Installation

### As a Standalone Script
```bash
# Make executable
chmod +x quantum_hydra.py

# Run directly
python quantum_hydra.py
```

### As a Python Package
```bash
# Install in development mode
pip install -e .

# Or install normally
pip install .

# Or install from PyPI (once published)
pip install quantum-hydra-cipher
```

### Command Aliases
After installation, you can run the cipher using either command:
```bash
quantum-hydra    # Full command
qhc              # Short alias (Quantum Hydra Cipher)
```

## Usage

### Interactive Mode
```bash
python quantum_hydra.py
```

Follow the on-screen prompts to:
1. Choose encryption or decryption
2. Specify the directory containing your files
3. Enter your master password
4. Confirm the operation

### Programmatic Usage
```python
from quantum_hydra import QuantumHydraCipherV3

# Initialize cipher with password
cipher = QuantumHydraCipherV3("your-secure-password")

# Encrypt text
plaintext = "Secret message"
encrypted, salt = cipher.encrypt_text(plaintext, "message.txt")

# Encrypt binary file
with open("image.jpg", "rb") as f:
    data = f.read()
encrypted, salt = cipher.encrypt_binary(data, "image.jpg")

# Decrypt
success, result = cipher.decrypt_data(encrypted, salt, is_binary=True)
```

## File Format

Encrypted files are saved with the `.qhc` extension (Quantum Hydra Cipher). These files contain:
- Original filename
- File type information
- Encryption timestamp
- Encrypted data
- Salt for key derivation
- Integrity checksums

## Security Warnings

⚠️ **IMPORTANT:**
- Original files are **PERMANENTLY DELETED** after encryption
- Encrypted files are **PERMANENTLY DELETED** after decryption
- **REMEMBER YOUR PASSWORD** - there is no recovery method
- Use strong, unique passwords for maximum security
- Keep backups of important files before encryption

## Example Workflow

### Encrypting Files
1. Place your files in a directory
2. Run the program and select "ENCODE"
3. Enter the directory path
4. Set a strong password
5. Original files are encrypted to `.qhc` format and deleted

### Decrypting Files
1. Place `.qhc` files in a directory
2. Run the program and select "DECODE"
3. Enter the directory path
4. Enter the same password used for encryption
5. Files are restored to original format and `.qhc` files are deleted

## Technical Details

### Encryption Process (Text Files)
1. Derive 64-byte key from password using PBKDF2-HMAC-SHA512
2. Apply polyalphabetic substitution using 52 shuffled alphabets
3. Compress using zlib (level 9)
4. Apply prime-based columnar transposition
5. XOR with SHA-512 keystream
6. Byte substitution using password-seeded S-Box
7. 8-round Feistel network shuffle
8. Add HMAC-SHA256 and CRC32 for integrity

### Encryption Process (Binary Files)
Same as text files, but skips step 2 (polyalphabetic substitution) as it only applies to text.

## Requirements

- Python 3.7 or higher
- No external dependencies (uses only standard library)

## Author

**Muhammad Sufiyan Baig**
- Email: send.sufiyan@gmail.com
- GitHub: [@muhammadsufiyanbaig](https://github.com/muhammadsufiyanbaig)

## License

This software is provided as-is for educational and personal use under the MIT License.

Copyright (c) 2026 Muhammad Sufiyan Baig

## Version History

- **v3.0** - Added multi-format support (PDF, images, video, audio)
- **v2.0** - Multi-file processing with auto-delete
- **v1.0** - Initial 7-layer cipher implementation
