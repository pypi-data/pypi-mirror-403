# Quantum Hydra Cipher - Changelog

## Version 3.0 (2026-01-30)

### Major Features Added

#### 1. Multi-Format File Support
- **PDF Support**: Full encryption/decryption of PDF documents
- **Image Support**: JPG, JPEG, PNG, GIF, BMP, WEBP, TIFF, ICO
- **Video Support**: MP4, MOV, AVI, MKV, WEBM, FLV, WMV, M4V
- **Audio Support**: MP3, WAV, FLAC, AAC, OGG, M4A, WMA, OPUS

#### 2. Enhanced Encryption System
- Added `encrypt_binary()` method for non-text files
- Binary files use 6 encryption layers (skips polyalphabetic substitution)
- Maintains all security features for binary data
- Automatic file type detection

#### 3. Improved File Handling
- `detect_file_type()` function automatically identifies file types
- File type stored in .qhc metadata
- Proper restoration of original file extensions
- Support for case-insensitive extension matching

#### 4. Package Structure
- Created proper Python package with `setup.py`
- Entry point: `quantum-hydra` command after installation
- Modular architecture for easy integration
- Can be imported as a library in other Python projects

#### 5. Documentation & Testing
- Comprehensive README.md with installation and usage
- USAGE_EXAMPLES.md with real-world scenarios
- Complete test suite (`test_quantum_hydra.py`)
- All tests passing (5/5)

### Technical Improvements

#### Encryption Layers
**Text Files (7 layers):**
1. PBKDF2 Key Derivation (150,000 iterations)
2. Polyalphabetic Vigenère substitution
3. Columnar Transposition
4. XOR Stream Cipher
5. S-Box Substitution
6. Feistel Network (8 rounds)
7. HMAC-SHA256 + CRC32

**Binary Files (6 layers):**
- Same as text but skips layer 2 (polyalphabetic)
- Optimized for binary data integrity

#### File Format Updates
.qhc files now include:
- File type metadata (text/pdf/image/video/audio)
- File extension information
- Version 3.0 header
- Enhanced integrity checking

### Code Changes

#### New Functions
```python
- detect_file_type(filename) -> str
- get_supported_extensions() -> List[str]
- encrypt_binary(data, filename) -> Tuple[bytes, bytes]
```

#### Modified Functions
```python
- encrypt_text() - unchanged signature, improved internals
- decrypt_data() - added is_binary parameter
- create_qhc_file() - added file_type parameter
- read_qhc_file() - returns file_type now
- encode_files() - handles all supported formats
- decode_files() - restores files to original format
```

#### Class Updates
- Renamed: `QuantumHydraCipherV2` → `QuantumHydraCipherV3`
- All existing methods remain compatible
- New binary encryption methods added

### User Interface Updates

#### Main Menu
- Added option [3] to show supported formats
- Updated descriptions to reflect multi-format support
- Better warning messages
- Enhanced visual feedback

#### Console Output
- Shows file type during processing
- Displays layer count (6 or 7) during encryption
- Better progress indicators
- Clear success/failure messages

### Backward Compatibility

#### v2.0 .qhc files
- Can still be read by v3.0
- Missing TYPE field defaults to "text"
- Full backward compatibility maintained

#### API Compatibility
- All v2.0 methods still work
- New parameters are optional
- Existing scripts don't need updates

### Security Enhancements

#### Binary File Security
- Maintained 150,000 PBKDF2 iterations
- Same HMAC-SHA256 authentication
- CRC32 integrity checking for all files
- Secure compression before encryption

#### File Type Validation
- Extension checking before encryption
- Type verification during decryption
- Prevents format confusion attacks

### Performance

#### Benchmarks (approximate)
- Text (1 KB): < 0.1 seconds
- Image (5 MB): 1-2 seconds
- Video (100 MB): 10-20 seconds
- PDF (10 MB): 2-3 seconds
- Audio (5 MB): 1-2 seconds

*Times vary based on system performance*

### Testing

#### Test Coverage
✅ Text encryption/decryption
✅ Binary encryption/decryption
✅ Wrong password detection
✅ File type detection
✅ QHC file format handling

All tests passing with 100% success rate.

### Installation

#### As Package
```bash
pip install -e .
quantum-hydra
```

#### Standalone
```bash
python quantum_hydra.py
```

### Migration from v2.0

#### No changes required for:
- Existing .qhc files (fully compatible)
- Encryption passwords (same algorithm)
- Command-line usage (same interface)

#### Benefits of upgrading:
- Support for non-text files
- Better metadata tracking
- More robust file handling
- Comprehensive documentation

### Known Limitations

1. Very large files (> 1 GB) may take several minutes
2. Encrypted files are larger due to compression and overhead
3. Password cannot be recovered if forgotten
4. Original files are permanently deleted after encryption

### Future Roadmap (v4.0)

Potential features for next version:
- Folder encryption
- Compression level selection
- Password strength meter
- GUI interface
- Cloud storage integration
- Key file support
- Multi-threading for large files

---

## Version 2.0 (Previous)

- Multi-file processing
- Auto-delete feature
- 7-layer encryption for text files
- .qhc file format
- Interactive CLI

## Version 1.0 (Original)

- Single file encryption
- Basic 7-layer cipher
- Text file support only
- Command-line interface

---

**Note**: This cipher is for educational and personal use. For production environments, consider using established cryptographic libraries like NaCl/libsodium or GPG.
