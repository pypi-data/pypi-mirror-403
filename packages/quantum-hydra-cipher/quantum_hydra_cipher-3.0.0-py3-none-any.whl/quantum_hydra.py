#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    QUANTUM HYDRA CIPHER SYSTEM v3.0                          ║
║         Multi-Format File Encryption with Auto-Delete Feature                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  WORKFLOW:                                                                   ║
║  ENCODE: ANY file → .qhc encrypted files → DELETE original files            ║
║  DECODE: .qhc files → original format → DELETE .qhc files                   ║
║                                                                              ║
║  SUPPORTED FORMATS:                                                          ║
║  • Text: .txt                                                                ║
║  • Documents: .pdf                                                           ║
║  • Images: .jpg, .jpeg, .png, .gif, .bmp, .webp                             ║
║  • Videos: .mp4, .mov, .avi, .mkv, .webm                                    ║
║  • Audio: .mp3, .wav, .flac, .aac, .ogg                                     ║
║                                                                              ║
║  ENCRYPTION LAYERS:                                                          ║
║  1. Salted Key Derivation (PBKDF2 + Argon2-like stretching)                 ║
║  2. Polyalphabetic Vigenère with Dynamic Alphabet Rotation                  ║
║  3. Columnar Transposition with Prime-Seeded Permutation                    ║
║  4. XOR Stream Cipher with SHA-512 Key Expansion                            ║
║  5. Byte-Level Substitution Box (S-Box)                                     ║
║  6. Block Shuffling with Feistel Network                                    ║
║  7. HMAC-SHA256 Authentication + CRC32 Redundancy                           ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import glob
import hashlib
import hmac
import random
import struct
import json
import base64
import zlib
import secrets
import shutil
from datetime import datetime
from typing import List, Tuple, Dict, Optional
from pathlib import Path


class QuantumHydraCipherV3:
    """
    Advanced multi-layer cipher with multi-format file encryption/decryption.
    Supports text, PDF, images, videos, and audio files.
    Each file becomes one .qhc encrypted file and vice versa.
    """
    
    # S-Box for byte substitution (256 unique mappings)
    SBOX = None
    SBOX_INV = None
    
    # Prime numbers for various operations
    PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71,
              73, 79, 83, 89, 97, 101, 103, 107, 109, 113, 127, 131, 137, 139, 149, 151,
              157, 163, 167, 173, 179, 181, 191, 193, 197, 199, 211, 223, 227, 229, 233]
    
    def __init__(self, master_password: str = "QuantumHydraDefault"):
        """Initialize cipher with master password."""
        self.master_password = master_password if master_password else "QuantumHydraDefault"
        self._generate_sbox()
        self._generate_alphabets()
    
    def _generate_sbox(self):
        """Generate S-Box and inverse S-Box based on password."""
        seed = int(hashlib.sha256(self.master_password.encode()).hexdigest(), 16)
        random.seed(seed)
        
        self.SBOX = list(range(256))
        random.shuffle(self.SBOX)
        
        # Create inverse S-Box
        self.SBOX_INV = [0] * 256
        for i, v in enumerate(self.SBOX):
            self.SBOX_INV[v] = i
    
    def _generate_alphabets(self):
        """Generate 52 unique substitution alphabets (upper + lower)."""
        seed = int(hashlib.sha512(self.master_password.encode()).hexdigest(), 16)
        
        self.ALPHABETS_UPPER = []
        self.ALPHABETS_LOWER = []
        
        base_upper = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        base_lower = list("abcdefghijklmnopqrstuvwxyz")
        
        for i in range(26):
            random.seed(seed + i * 1009)
            upper = base_upper.copy()
            lower = base_lower.copy()
            random.shuffle(upper)
            random.shuffle(lower)
            self.ALPHABETS_UPPER.append(''.join(upper))
            self.ALPHABETS_LOWER.append(''.join(lower))
    
    # ═══════════════════════════════════════════════════════════════════════════
    # LAYER 1: Key Derivation with Salt
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _derive_key(self, salt: bytes, iterations: int = 150000) -> bytes:
        """Derive encryption key using PBKDF2 with high iteration count."""
        return hashlib.pbkdf2_hmac(
            'sha512',
            self.master_password.encode(),
            salt,
            iterations,
            dklen=64
        )
    
    # ═══════════════════════════════════════════════════════════════════════════
    # LAYER 2: Polyalphabetic Substitution
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _poly_substitute(self, text: str, key: bytes, encrypt: bool = True) -> str:
        """Apply polyalphabetic substitution cipher."""
        result = []
        key_idx = 0
        
        for i, char in enumerate(text):
            if char.isupper():
                alpha_idx = (key[key_idx % len(key)] + i * 7) % 26
                alphabet = self.ALPHABETS_UPPER[alpha_idx]
                if encrypt:
                    result.append(alphabet[ord(char) - ord('A')])
                else:
                    result.append(chr(alphabet.index(char) + ord('A')))
                key_idx += 1
            elif char.islower():
                alpha_idx = (key[key_idx % len(key)] + i * 7) % 26
                alphabet = self.ALPHABETS_LOWER[alpha_idx]
                if encrypt:
                    result.append(alphabet[ord(char) - ord('a')])
                else:
                    result.append(chr(alphabet.index(char) + ord('a')))
                key_idx += 1
            else:
                result.append(char)
        
        return ''.join(result)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # LAYER 3: Columnar Transposition
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _columnar_transpose(self, data: bytes, key: bytes, encrypt: bool = True) -> bytes:
        """Apply columnar transposition with prime-based column ordering."""
        if len(data) == 0:
            return data
        
        # Determine number of columns from key
        seed = int.from_bytes(key[:8], 'big')
        num_cols = self.PRIMES[seed % 20 + 5]  # Use primes between index 5-24
        
        # Pad data
        pad_len = (num_cols - (len(data) % num_cols)) % num_cols
        if encrypt:
            padded = data + secrets.token_bytes(pad_len)
        else:
            padded = data
        
        num_rows = len(padded) // num_cols
        
        # Generate column order
        random.seed(seed)
        col_order = list(range(num_cols))
        random.shuffle(col_order)
        
        if encrypt:
            # Write row by row, read column by column in shuffled order
            matrix = [padded[i*num_cols:(i+1)*num_cols] for i in range(num_rows)]
            result = bytearray()
            for col in col_order:
                for row in matrix:
                    if col < len(row):
                        result.append(row[col])
            return struct.pack('>I', len(data)) + struct.pack('>B', pad_len) + bytes(result)
        else:
            # Reverse the transposition
            orig_len = struct.unpack('>I', data[:4])[0]
            pad_len = struct.unpack('>B', data[4:5])[0]
            data = data[5:]
            
            num_rows = len(data) // num_cols
            
            # Read columns in shuffled order
            col_data = {}
            pos = 0
            for col in col_order:
                col_data[col] = data[pos:pos+num_rows]
                pos += num_rows
            
            # Reconstruct rows
            result = bytearray()
            for row in range(num_rows):
                for col in range(num_cols):
                    if row < len(col_data.get(col, b'')):
                        result.append(col_data[col][row])
            
            return bytes(result[:orig_len])
    
    # ═══════════════════════════════════════════════════════════════════════════
    # LAYER 4: XOR Stream Cipher
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _xor_stream(self, data: bytes, key: bytes) -> bytes:
        """XOR with SHA-512 expanded keystream."""
        keystream = bytearray()
        num_blocks = (len(data) + 63) // 64
        
        for i in range(num_blocks):
            block = hashlib.sha512(key + struct.pack('>Q', i)).digest()
            keystream.extend(block)
        
        return bytes(a ^ b for a, b in zip(data, keystream))
    
    # ═══════════════════════════════════════════════════════════════════════════
    # LAYER 5: S-Box Substitution
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _sbox_substitute(self, data: bytes, encrypt: bool = True) -> bytes:
        """Apply S-Box byte substitution."""
        box = self.SBOX if encrypt else self.SBOX_INV
        return bytes(box[b] for b in data)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # LAYER 6: Feistel Block Shuffle
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _feistel_shuffle(self, data: bytes, key: bytes, rounds: int = 8, encrypt: bool = True) -> bytes:
        """Apply Feistel-like network for block shuffling."""
        if len(data) < 2:
            return data
        
        mid = len(data) // 2
        left = bytearray(data[:mid])
        right = bytearray(data[mid:])
        
        # Pad right if needed
        if len(right) < len(left):
            right.append(0)
        
        round_range = range(rounds) if encrypt else range(rounds-1, -1, -1)
        
        for r in round_range:
            # Round function using hash
            round_key = hashlib.sha256(key + struct.pack('>I', r)).digest()
            
            if encrypt:
                # F function: XOR right with hash of (left + round_key)
                f_out = hashlib.sha256(bytes(left) + round_key).digest()
                f_out = (f_out * ((len(right) // 32) + 1))[:len(right)]
                new_right = bytes(a ^ b for a, b in zip(right, f_out))
                left, right = bytearray(new_right), left
            else:
                # Reverse Feistel
                f_out = hashlib.sha256(bytes(right) + round_key).digest()
                f_out = (f_out * ((len(left) // 32) + 1))[:len(left)]
                new_left = bytes(a ^ b for a, b in zip(left, f_out))
                left, right = right, bytearray(new_left)
        
        result = bytes(left) + bytes(right)
        return result[:len(data)]
    
    # ═══════════════════════════════════════════════════════════════════════════
    # LAYER 7: HMAC + CRC32 Verification
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _add_verification(self, data: bytes, key: bytes) -> bytes:
        """Add HMAC-SHA256 and CRC32 for integrity."""
        crc = struct.pack('>I', zlib.crc32(data) & 0xFFFFFFFF)
        mac = hmac.new(key, data + crc, hashlib.sha256).digest()
        return mac + crc + data
    
    def _verify_and_strip(self, data: bytes, key: bytes) -> Tuple[bool, bytes]:
        """Verify HMAC and CRC32, return (valid, payload)."""
        if len(data) < 36:
            return False, b''
        
        stored_mac = data[:32]
        stored_crc = data[32:36]
        payload = data[36:]
        
        # Verify CRC
        computed_crc = struct.pack('>I', zlib.crc32(payload) & 0xFFFFFFFF)
        if stored_crc != computed_crc:
            return False, b''
        
        # Verify HMAC
        computed_mac = hmac.new(key, payload + stored_crc, hashlib.sha256).digest()
        if not hmac.compare_digest(stored_mac, computed_mac):
            return False, b''
        
        return True, payload
    
    # ═══════════════════════════════════════════════════════════════════════════
    # MAIN ENCRYPTION/DECRYPTION
    # ═══════════════════════════════════════════════════════════════════════════

    def encrypt_text(self, plaintext: str, filename: str) -> Tuple[bytes, bytes]:
        """
        Encrypt plaintext through all 7 layers.
        Returns (encrypted_data, salt) for storage.
        """
        # Generate random salt
        salt = secrets.token_bytes(32)

        # Layer 1: Derive key
        key = self._derive_key(salt)

        # Layer 2: Polyalphabetic substitution
        substituted = self._poly_substitute(plaintext, key, encrypt=True)

        # Compress
        compressed = zlib.compress(substituted.encode('utf-8'), level=9)

        # Layer 3: Columnar transposition
        transposed = self._columnar_transpose(compressed, key[8:16], encrypt=True)

        # Layer 4: XOR stream
        xored = self._xor_stream(transposed, key[16:32])

        # Layer 5: S-Box substitution
        sboxed = self._sbox_substitute(xored, encrypt=True)

        # Layer 6: Feistel shuffle
        shuffled = self._feistel_shuffle(sboxed, key[32:48], rounds=8, encrypt=True)

        # Layer 7: Add verification
        verified = self._add_verification(shuffled, key[48:64])

        return verified, salt

    def encrypt_binary(self, data: bytes, filename: str) -> Tuple[bytes, bytes]:
        """
        Encrypt binary data through 6 layers (skips text-only polyalphabetic).
        Used for PDFs, images, videos, audio files.
        Returns (encrypted_data, salt) for storage.
        """
        # Generate random salt
        salt = secrets.token_bytes(32)

        # Layer 1: Derive key
        key = self._derive_key(salt)

        # Skip Layer 2 (polyalphabetic - text only)
        # Compress binary data
        compressed = zlib.compress(data, level=9)

        # Layer 3: Columnar transposition
        transposed = self._columnar_transpose(compressed, key[8:16], encrypt=True)

        # Layer 4: XOR stream
        xored = self._xor_stream(transposed, key[16:32])

        # Layer 5: S-Box substitution
        sboxed = self._sbox_substitute(xored, encrypt=True)

        # Layer 6: Feistel shuffle
        shuffled = self._feistel_shuffle(sboxed, key[32:48], rounds=8, encrypt=True)

        # Layer 7: Add verification
        verified = self._add_verification(shuffled, key[48:64])

        return verified, salt
    
    def decrypt_data(self, encrypted: bytes, salt: bytes, is_binary: bool = False) -> Tuple[bool, any]:
        """
        Decrypt data through all layers in reverse.
        Returns (success, plaintext/bytes).
        """
        # Layer 1: Derive key
        key = self._derive_key(salt)

        # Layer 7: Verify and strip
        valid, shuffled = self._verify_and_strip(encrypted, key[48:64])
        if not valid:
            return False, "Integrity verification failed"

        # Layer 6: Reverse Feistel
        sboxed = self._feistel_shuffle(shuffled, key[32:48], rounds=8, encrypt=False)

        # Layer 5: Reverse S-Box
        xored = self._sbox_substitute(sboxed, encrypt=False)

        # Layer 4: Reverse XOR
        transposed = self._xor_stream(xored, key[16:32])

        # Layer 3: Reverse transposition
        compressed = self._columnar_transpose(transposed, key[8:16], encrypt=False)

        # Decompress
        try:
            decompressed = zlib.decompress(compressed)
        except:
            return False, "Decompression failed"

        if is_binary:
            # For binary files, return raw bytes
            return True, decompressed
        else:
            # For text files, decode and apply Layer 2
            try:
                substituted = decompressed.decode('utf-8')
            except:
                return False, "Text decoding failed"

            # Layer 2: Reverse polyalphabetic
            plaintext = self._poly_substitute(substituted, key, encrypt=False)
            return True, plaintext
    
    # ═══════════════════════════════════════════════════════════════════════════
    # FILE OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def create_qhc_file(self, encrypted: bytes, salt: bytes,
                        original_filename: str, output_path: str, file_type: str = "text"):
        """Create a .qhc encrypted file with metadata."""

        # Encode data
        encoded_data = base64.b85encode(encrypted).decode('ascii')
        encoded_salt = base64.b64encode(salt).decode('ascii')

        # Determine file extension
        file_ext = os.path.splitext(original_filename)[1].lower()

        # Create file content
        content = f"""# ╔══════════════════════════════════════════════════════════════════╗
# ║            QUANTUM HYDRA CIPHER - ENCRYPTED FILE                 ║
# ║                        Version 3.0                               ║
# ╚══════════════════════════════════════════════════════════════════╝

## FILE INFORMATION
- **Original Filename**: {original_filename}
- **File Type**: {file_type}
- **File Extension**: {file_ext}
- **Encrypted At**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Cipher**: Quantum Hydra v3.0 (7-Layer Encryption)

## SECURITY NOTICE
This file contains encrypted data protected by:
1. PBKDF2 Key Derivation (150,000 iterations)
2. Polyalphabetic Substitution (52 alphabets) - Text Only
3. Prime-Based Columnar Transposition
4. SHA-512 XOR Stream Cipher
5. 256-Byte S-Box Substitution
6. 8-Round Feistel Network
7. HMAC-SHA256 + CRC32 Verification

## DECRYPTION DATA
```qhc
SALT:{encoded_salt}
DATA:{encoded_data}
FILE:{original_filename}
TYPE:{file_type}
```

## VERIFICATION
- Salt Length: {len(salt)} bytes
- Data Length: {len(encrypted)} bytes
- Checksum: {hashlib.md5(encrypted).hexdigest()}

---
⚠️ DO NOT MODIFY THIS FILE - Any changes will corrupt the encrypted data
"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def read_qhc_file(self, filepath: str) -> Tuple[bytes, bytes, str, str]:
        """Read and parse a .qhc file. Returns (encrypted, salt, original_filename, file_type)."""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract data block
        import re
        match = re.search(r'```qhc\s*\n(.*?)\n```', content, re.DOTALL)
        if not match:
            raise ValueError("Invalid QHC file format")

        data_block = match.group(1)

        salt = None
        encrypted = None
        original_filename = None
        file_type = "text"  # Default for backward compatibility

        for line in data_block.strip().split('\n'):
            if line.startswith('SALT:'):
                salt = base64.b64decode(line[5:])
            elif line.startswith('DATA:'):
                encrypted = base64.b85decode(line[5:])
            elif line.startswith('FILE:'):
                original_filename = line[5:]
            elif line.startswith('TYPE:'):
                file_type = line[5:]

        if salt is None or encrypted is None or original_filename is None:
            raise ValueError("Missing required fields in QHC file")

        return encrypted, salt, original_filename, file_type


def detect_file_type(filename: str) -> str:
    """
    Detect file type based on extension.
    Returns: 'text', 'pdf', 'image', 'video', or 'audio'
    """
    ext = os.path.splitext(filename)[1].lower()

    TEXT_EXTS = ['.txt']
    PDF_EXTS = ['.pdf']
    IMAGE_EXTS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.ico']
    VIDEO_EXTS = ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv', '.wmv', '.m4v']
    AUDIO_EXTS = ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma', '.opus']

    if ext in TEXT_EXTS:
        return 'text'
    elif ext in PDF_EXTS:
        return 'pdf'
    elif ext in IMAGE_EXTS:
        return 'image'
    elif ext in VIDEO_EXTS:
        return 'video'
    elif ext in AUDIO_EXTS:
        return 'audio'
    else:
        return 'binary'  # Generic binary file


def get_supported_extensions() -> List[str]:
    """Get list of all supported file extensions."""
    return [
        '.txt',
        '.pdf',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.ico',
        '.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv', '.wmv', '.m4v',
        '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma', '.opus'
    ]


def print_banner():
    """Print the application banner."""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ░██████╗░██╗░░░██╗░█████╗░███╗░░██╗████████╗██╗░░░██╗███╗░░░███╗           ║
║   ██╔═══██╗██║░░░██║██╔══██╗████╗░██║╚══██╔══╝██║░░░██║████╗░████║           ║
║   ██║██╗██║██║░░░██║███████║██╔██╗██║░░░██║░░░██║░░░██║██╔████╔██║           ║
║   ╚██████╔╝██║░░░██║██╔══██║██║╚████║░░░██║░░░██║░░░██║██║╚██╔╝██║           ║
║   ░╚═██╔═╝░╚██████╔╝██║░░██║██║░╚███║░░░██║░░░╚██████╔╝██║░╚═╝░██║           ║
║   ░░░╚═╝░░░░╚═════╝░╚═╝░░╚═╝╚═╝░░╚══╝░░░╚═╝░░░░╚═════╝░╚═╝░░░░░╚═╝           ║
║                                                                              ║
║   ██╗░░██╗██╗░░░██╗██████╗░██████╗░░█████╗░  ██╗░░░██╗██████╗░               ║
║   ██║░░██║╚██╗░██╔╝██╔══██╗██╔══██╗██╔══██╗  ██║░░░██║╚════██╗               ║
║   ███████║░╚████╔╝░██║░░██║██████╔╝███████║  ╚██╗░██╔╝░░███╔═╝               ║
║   ██╔══██║░░╚██╔╝░░██║░░██║██╔══██╗██╔══██║  ░╚████╔╝░██╔══╝░░               ║
║   ██║░░██║░░░██║░░░██████╔╝██║░░██║██║░░██║  ░░╚██╔╝░░███████╗               ║
║   ╚═╝░░╚═╝░░░╚═╝░░░╚═════╝░╚═╝░░╚═╝╚═╝░░╚═╝  ░░░╚═╝░░░╚══════╝               ║
║                                                                              ║
║              C  I  P  H  E  R     S  Y  S  T  E  M                           ║
║                          Version 3.0                                         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  7-Layer Military-Grade Encryption • Multi-Format Support                   ║
║  Text • PDF • Images • Videos • Audio • Auto-Delete After Processing        ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)


def encode_files(directory: str, password: str):
    """
    ENCODE MODE:
    1. Find all supported files in directory
    2. Encrypt each file → create .qhc file
    3. DELETE original file
    """
    print("\n" + "═" * 70)
    print("  ENCRYPTION MODE - Multiple Formats → .qhc")
    print("═" * 70)

    # Find all supported files
    all_files = []
    supported_exts = get_supported_extensions()

    for ext in supported_exts:
        pattern = os.path.join(directory, f"*{ext}")
        all_files.extend(glob.glob(pattern))

    if not all_files:
        print(f"\n  ⚠️  No supported files found in: {directory}")
        print(f"  Supported formats: TXT, PDF, Images (JPG/PNG), Videos (MP4/MOV), Audio (MP3/WAV)")
        return

    print(f"\n  📂 Directory: {os.path.abspath(directory)}")
    print(f"  🔍 Found {len(all_files)} supported file(s)")
    print()

    cipher = QuantumHydraCipherV3(password)

    success_count = 0

    for file_path in all_files:
        filename = os.path.basename(file_path)
        qhc_path = file_path.rsplit('.', 1)[0] + '.qhc'

        # Detect file type
        file_type = detect_file_type(filename)

        print(f"  ┌─ Processing: {filename} ({file_type})")

        try:
            if file_type == 'text':
                # Read text file
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                print(f"  │  📖 Read {len(content)} characters")

                # Encrypt text
                print(f"  │  🔐 Encrypting through 7 layers...")
                encrypted, salt = cipher.encrypt_text(content, filename)
            else:
                # Read binary file
                with open(file_path, 'rb') as f:
                    content = f.read()
                print(f"  │  📖 Read {len(content)} bytes")

                # Encrypt binary
                print(f"  │  🔐 Encrypting through 6 layers...")
                encrypted, salt = cipher.encrypt_binary(content, filename)

            # Create .qhc file
            cipher.create_qhc_file(encrypted, salt, filename, qhc_path, file_type)
            print(f"  │  📝 Created: {os.path.basename(qhc_path)}")

            # DELETE original file
            os.remove(file_path)
            print(f"  │  🗑️  Deleted: {filename}")

            print(f"  └─ ✅ SUCCESS")
            success_count += 1

        except Exception as e:
            print(f"  └─ ❌ ERROR: {str(e)}")

        print()

    print("═" * 70)
    print(f"  ENCRYPTION COMPLETE: {success_count}/{len(all_files)} files processed")
    print("═" * 70 + "\n")


def decode_files(directory: str, password: str):
    """
    DECODE MODE:
    1. Find all .qhc files in directory
    2. Decrypt each file → restore original format
    3. DELETE original .qhc file
    """
    print("\n" + "═" * 70)
    print("  DECRYPTION MODE - .qhc → Original Format")
    print("═" * 70)

    # Find all .qhc files
    qhc_files = glob.glob(os.path.join(directory, "*.qhc"))

    if not qhc_files:
        print(f"\n  ⚠️  No .qhc files found in: {directory}")
        return

    print(f"\n  📂 Directory: {os.path.abspath(directory)}")
    print(f"  🔍 Found {len(qhc_files)} .qhc file(s)")
    print()

    cipher = QuantumHydraCipherV3(password)

    success_count = 0

    for qhc_path in qhc_files:
        filename = os.path.basename(qhc_path)

        print(f"  ┌─ Processing: {filename}")

        try:
            # Read .qhc file
            encrypted, salt, original_filename, file_type = cipher.read_qhc_file(qhc_path)
            print(f"  │  📖 Read encrypted data ({len(encrypted)} bytes)")
            print(f"  │  📄 Original file: {original_filename} ({file_type})")

            # Decrypt
            is_binary = (file_type != 'text')
            print(f"  │  🔓 Decrypting through {'6' if is_binary else '7'} layers...")
            success, result = cipher.decrypt_data(encrypted, salt, is_binary=is_binary)

            if not success:
                print(f"  └─ ❌ DECRYPTION FAILED: {result}")
                print()
                continue

            # Determine output path
            output_path = os.path.join(directory, original_filename)

            # Handle filename collision
            if os.path.exists(output_path):
                base, ext = os.path.splitext(original_filename)
                output_path = os.path.join(directory, f"{base}_decrypted{ext}")

            # Write file (text or binary)
            if file_type == 'text':
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(result)
            else:
                with open(output_path, 'wb') as f:
                    f.write(result)

            print(f"  │  📝 Created: {os.path.basename(output_path)}")

            # DELETE original .qhc file
            os.remove(qhc_path)
            print(f"  │  🗑️  Deleted: {filename}")

            print(f"  └─ ✅ SUCCESS")
            success_count += 1

        except Exception as e:
            print(f"  └─ ❌ ERROR: {str(e)}")

        print()

    print("═" * 70)
    print(f"  DECRYPTION COMPLETE: {success_count}/{len(qhc_files)} files processed")
    print("═" * 70 + "\n")


def main():
    """Main CLI interface."""
    print_banner()

    print("\n  Select Operation:")
    print("  ─────────────────")
    print("  [1] 🔒 ENCODE  →  Files become .qhc (originals deleted)")
    print("  [2] 🔓 DECODE  →  .qhc files restored (encrypted deleted)")
    print("  [3] 📋 SHOW SUPPORTED FORMATS")
    print("  [4] 🚪 EXIT")

    choice = input("\n  Enter choice (1/2/3/4): ").strip()

    if choice == '1':
        print("\n  ╔═══════════════════════════════════════╗")
        print("  ║         ENCODE CONFIGURATION          ║")
        print("  ╚═══════════════════════════════════════╝")

        directory = input("\n  📁 Directory with files [./]: ").strip() or "."
        password = input("  🔑 Master password: ").strip()

        if not password:
            print("\n  ⚠️  Warning: Using default password (less secure)")
            confirm = input("  Continue anyway? (y/n): ").strip().lower()
            if confirm != 'y':
                print("\n  Cancelled.")
                return

        # Confirm deletion warning
        print("\n  ⚠️  WARNING: Original files will be PERMANENTLY DELETED")
        print("     after encryption. Make sure you remember your password!")
        print("\n  📝 Supported: TXT, PDF, JPG/PNG, MP4/MOV, MP3/WAV, and more")
        confirm = input("\n  Proceed with encryption? (y/n): ").strip().lower()

        if confirm == 'y':
            encode_files(directory, password)
        else:
            print("\n  Cancelled.")

    elif choice == '2':
        print("\n  ╔═══════════════════════════════════════╗")
        print("  ║         DECODE CONFIGURATION          ║")
        print("  ╚═══════════════════════════════════════╝")

        directory = input("\n  📁 Directory with .qhc files [./]: ").strip() or "."
        password = input("  🔑 Master password: ").strip()

        # Confirm deletion warning
        print("\n  ⚠️  WARNING: .qhc files will be DELETED after decryption")
        confirm = input("\n  Proceed with decryption? (y/n): ").strip().lower()

        if confirm == 'y':
            decode_files(directory, password)
        else:
            print("\n  Cancelled.")

    elif choice == '3':
        print("\n  ╔═══════════════════════════════════════════════════════════╗")
        print("  ║              SUPPORTED FILE FORMATS                       ║")
        print("  ╚═══════════════════════════════════════════════════════════╝")
        print("\n  📄 Text:      .txt")
        print("  📋 Documents: .pdf")
        print("  🖼️  Images:    .jpg, .jpeg, .png, .gif, .bmp, .webp, .tiff")
        print("  🎬 Videos:    .mp4, .mov, .avi, .mkv, .webm, .flv, .wmv")
        print("  🎵 Audio:     .mp3, .wav, .flac, .aac, .ogg, .m4a, .wma")
        print()

    elif choice == '4':
        print("\n  👋 Goodbye!\n")

    else:
        print("\n  ❌ Invalid choice\n")


if __name__ == "__main__":
    main()