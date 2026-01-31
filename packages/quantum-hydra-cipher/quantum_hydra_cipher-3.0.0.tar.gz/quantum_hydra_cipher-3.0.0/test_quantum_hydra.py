#!/usr/bin/env python3
"""
Test script for Quantum Hydra Cipher v3.0
Demonstrates encryption and decryption of various file types
"""

import os
import sys
from quantum_hydra import QuantumHydraCipherV3

def test_text_encryption():
    """Test text encryption and decryption."""
    print("\n" + "="*60)
    print("TEST 1: Text Encryption")
    print("="*60)

    cipher = QuantumHydraCipherV3("test-password-123")

    # Test data
    plaintext = "This is a secret message!\nMultiple lines are supported.\nSpecial chars: @#$%"
    filename = "test_message.txt"

    # Encrypt
    print(f"Original text ({len(plaintext)} chars):")
    print(f"  {plaintext[:50]}...")

    encrypted, salt = cipher.encrypt_text(plaintext, filename)
    print(f"\nEncrypted: {len(encrypted)} bytes")

    # Decrypt
    success, decrypted = cipher.decrypt_data(encrypted, salt, is_binary=False)

    if success and decrypted == plaintext:
        print("[PASS] Text encryption/decryption: PASSED")
        return True
    else:
        print("[FAIL] Text encryption/decryption: FAILED")
        return False


def test_binary_encryption():
    """Test binary data encryption and decryption."""
    print("\n" + "="*60)
    print("TEST 2: Binary Encryption")
    print("="*60)

    cipher = QuantumHydraCipherV3("test-password-456")

    # Create test binary data (simulating an image)
    import random
    random.seed(42)
    binary_data = bytes([random.randint(0, 255) for _ in range(1000)])
    filename = "test_image.jpg"

    print(f"Original binary data: {len(binary_data)} bytes")
    print(f"  First 20 bytes: {binary_data[:20].hex()}")

    # Encrypt
    encrypted, salt = cipher.encrypt_binary(binary_data, filename)
    print(f"\nEncrypted: {len(encrypted)} bytes")

    # Decrypt
    success, decrypted = cipher.decrypt_data(encrypted, salt, is_binary=True)

    if success and decrypted == binary_data:
        print("[PASS] Binary encryption/decryption: PASSED")
        return True
    else:
        print("[FAIL] Binary encryption/decryption: FAILED")
        return False


def test_wrong_password():
    """Test that wrong password fails decryption."""
    print("\n" + "="*60)
    print("TEST 3: Wrong Password Detection")
    print("="*60)

    # Encrypt with one password
    cipher1 = QuantumHydraCipherV3("correct-password")
    plaintext = "Secret data"
    encrypted, salt = cipher1.encrypt_text(plaintext, "test.txt")

    # Try to decrypt with wrong password
    cipher2 = QuantumHydraCipherV3("wrong-password")
    success, result = cipher2.decrypt_data(encrypted, salt, is_binary=False)

    if not success:
        print("[PASS] Wrong password correctly rejected: PASSED")
        return True
    else:
        print("[FAIL] Wrong password not detected: FAILED")
        return False


def test_file_type_detection():
    """Test file type detection."""
    print("\n" + "="*60)
    print("TEST 4: File Type Detection")
    print("="*60)

    from quantum_hydra import detect_file_type

    test_cases = [
        ("document.txt", "text"),
        ("image.jpg", "image"),
        ("video.mp4", "video"),
        ("audio.mp3", "audio"),
        ("document.pdf", "pdf"),
        ("photo.PNG", "image"),  # Test case insensitivity
    ]

    all_passed = True
    for filename, expected in test_cases:
        result = detect_file_type(filename)
        status = "[PASS]" if result == expected else "[FAIL]"
        print(f"  {status} {filename} -> {result} (expected: {expected})")
        if result != expected:
            all_passed = False

    if all_passed:
        print("\n[PASS] File type detection: PASSED")
        return True
    else:
        print("\n[FAIL] File type detection: FAILED")
        return False


def test_qhc_file_creation():
    """Test .qhc file creation and reading."""
    print("\n" + "="*60)
    print("TEST 5: QHC File Format")
    print("="*60)

    import tempfile
    import os

    cipher = QuantumHydraCipherV3("test-password")
    plaintext = "Test content"
    filename = "original.txt"

    # Encrypt
    encrypted, salt = cipher.encrypt_text(plaintext, filename)

    # Create temporary QHC file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.qhc', delete=False, encoding='utf-8') as f:
        temp_path = f.name

    try:
        # Write QHC file
        cipher.create_qhc_file(encrypted, salt, filename, temp_path, "text")
        print(f"Created QHC file: {os.path.basename(temp_path)}")

        # Read it back
        read_encrypted, read_salt, read_filename, read_type = cipher.read_qhc_file(temp_path)

        # Verify
        if (read_encrypted == encrypted and
            read_salt == salt and
            read_filename == filename and
            read_type == "text"):
            print("[PASS] QHC file creation/reading: PASSED")
            return True
        else:
            print("[FAIL] QHC file creation/reading: FAILED")
            return False
    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("QUANTUM HYDRA CIPHER v3.0 - TEST SUITE")
    print("="*60)

    tests = [
        test_text_encryption,
        test_binary_encryption,
        test_wrong_password,
        test_file_type_detection,
        test_qhc_file_creation,
    ]

    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"\n[FAIL] Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")

    if passed == total:
        print("\n*** All tests passed! ***")
        return 0
    else:
        print("\n*** Some tests failed ***")
        return 1


if __name__ == "__main__":
    sys.exit(main())
