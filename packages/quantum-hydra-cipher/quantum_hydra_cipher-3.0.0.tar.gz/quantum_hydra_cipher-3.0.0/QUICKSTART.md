# Quantum Hydra Cipher v3.0 - Quick Start Guide

## Installation

### Option 1: Run Directly (Recommended for first-time users)
```bash
cd "Quantum Hydra"
python quantum_hydra.py
```

### Option 2: Install as Package
```bash
cd "Quantum Hydra"
pip install -e .

# Run using either command:
quantum-hydra    # Full command
qhc              # Short alias
```

### Option 3: Install from PyPI (once published)
```bash
pip install quantum-hydra-cipher

# Run using either command:
quantum-hydra
qhc
```

## 5-Minute Tutorial

### Step 1: Create Test Files
```bash
# Create a test text file
echo "This is my secret message!" > test.txt

# Or use any existing file (PDF, image, video, audio)
```

### Step 2: Encrypt Files
1. Run: `python quantum_hydra.py`
2. Choose: `[1]` ENCODE
3. Enter directory: `.` (current directory)
4. Enter password: `MyTestPassword123`
5. Confirm: `y`

**Result**: `test.txt` → `test.qhc` (original deleted)

### Step 3: Decrypt Files
1. Run: `python quantum_hydra.py`
2. Choose: `[2]` DECODE
3. Enter directory: `.`
4. Enter password: `MyTestPassword123` (must match!)
5. Confirm: `y`

**Result**: `test.qhc` → `test.txt` (restored)

## Supported File Types

Run the program and choose option `[3]` to see all supported formats, or see below:

### Currently Supported
- **Text**: .txt
- **Documents**: .pdf
- **Images**: .jpg, .jpeg, .png, .gif, .bmp, .webp
- **Videos**: .mp4, .mov, .avi, .mkv, .webm
- **Audio**: .mp3, .wav, .flac, .aac, .ogg

## Basic Commands

### Interactive Mode
```bash
python quantum_hydra.py
```

### View Supported Formats
```bash
python quantum_hydra.py
# Choose [3] SHOW SUPPORTED FORMATS
```

### Run Tests
```bash
python test_quantum_hydra.py
```

## Common Use Cases

### Encrypt Photos
```bash
# Put photos in a folder, then:
python quantum_hydra.py
[1] ENCODE → ./photos → [password] → y
```

### Encrypt Videos
```bash
python quantum_hydra.py
[1] ENCODE → ./videos → [password] → y
```

### Encrypt Documents
```bash
python quantum_hydra.py
[1] ENCODE → ./documents → [password] → y
```

## Important Security Notes

⚠️ **CRITICAL WARNINGS**

1. **Original files are DELETED after encryption**
2. **No password recovery** - if you forget it, data is lost
3. **Keep backups** before encrypting important files
4. **Use strong passwords** (16+ characters recommended)

### Good Password Examples
- `Tr0pic@l!St0rm#2024`
- `MyS3cur3P@ssw0rd!XYZ`
- `Quantum_Hydra_2026!`

### Bad Password Examples
- `password` (too weak)
- `123456` (too weak)
- `myname` (too simple)

## Troubleshooting

### "No supported files found"
- Check file extensions
- Make sure files are in the specified directory
- Use option [3] to see supported formats

### "Decryption failed"
- Verify password is correct (case-sensitive)
- Check .qhc file isn't corrupted
- Ensure file was encrypted with compatible version

### "Permission denied"
- Close files if they're open in other programs
- Check folder permissions
- Run as administrator if needed (Windows)

## Next Steps

1. ✅ Try encrypting a test file
2. ✅ Verify you can decrypt it
3. ✅ Read USAGE_EXAMPLES.md for more scenarios
4. ✅ Check README.md for detailed documentation
5. ✅ Review security best practices

## Quick Reference

| Action | Command | Result |
|--------|---------|--------|
| Encrypt | Option [1] | Files → .qhc |
| Decrypt | Option [2] | .qhc → Files |
| Show formats | Option [3] | List supported types |
| Exit | Option [4] | Close program |

## Example Session

```
$ python quantum_hydra.py

╔════════════════════════════════════════╗
║   QUANTUM HYDRA v3.0 CIPHER SYSTEM     ║
╚════════════════════════════════════════╝

Select Operation:
[1] ENCODE → Files become .qhc
[2] DECODE → .qhc files restored
[3] SHOW SUPPORTED FORMATS
[4] EXIT

Enter choice (1/2/3/4): 1

Directory with files [./]: ./my_files
Master password: ********

⚠️  WARNING: Original files will be PERMANENTLY DELETED

Proceed with encryption? (y/n): y

Processing: photo.jpg (image)
  Read 1048576 bytes
  Encrypting through 6 layers...
  Created: photo.qhc
  Deleted: photo.jpg
  ✅ SUCCESS

ENCRYPTION COMPLETE: 1/1 files processed
```

## Getting Help

- Read README.md for full documentation
- Check USAGE_EXAMPLES.md for more examples
- Review CHANGELOG.md for version history
- Run tests: `python test_quantum_hydra.py`

## Programming Usage

```python
from quantum_hydra import QuantumHydraCipherV3

# Create cipher instance
cipher = QuantumHydraCipherV3("my-password")

# Encrypt text
text = "Secret message"
encrypted, salt = cipher.encrypt_text(text, "file.txt")

# Encrypt binary (images, videos, etc.)
with open("photo.jpg", "rb") as f:
    data = f.read()
encrypted, salt = cipher.encrypt_binary(data, "photo.jpg")

# Decrypt
success, result = cipher.decrypt_data(encrypted, salt, is_binary=True)
```

## System Requirements

- Python 3.7 or higher
- No external dependencies
- Works on Windows, Linux, macOS
- ~50 KB disk space

## License & Disclaimer

This software is provided as-is for educational and personal use. The authors are not responsible for data loss. Always keep backups of important files.

---

**Ready to start? Run `python quantum_hydra.py` now!**
