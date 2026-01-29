import pytest
import binascii
from redenv.crypto import (
    random_bytes,
    derive_key,
    encrypt,
    decrypt,
    buffer_to_hex,
    hex_to_buffer
)
from redenv.errors import RedenvError

# Inspect crypto.py to see available functions first. 
# I implemented: buffer_to_hex, hex_to_buffer, random_bytes, derive_key, encrypt, decrypt
# I did NOT implement generateRandomKey, exportKey, importKey because I used `cryptography` library which handles keys as bytes usually.
# However, TS uses CryptoKey objects.
# My `derive_key` returns `bytes`. `encrypt` takes `bytes`.
# This is fine as long as it's consistent.

def test_hex_conversion():
    original = b"hello world"
    hex_str = buffer_to_hex(original)
    restored = hex_to_buffer(hex_str)
    assert original == restored
    assert hex_str == binascii.hexlify(original).decode()

def test_random_bytes():
    b1 = random_bytes(32)
    b2 = random_bytes(32)
    assert len(b1) == 32
    assert len(b2) == 32
    assert b1 != b2

def test_derive_key_determinism():
    password = "password123"
    salt = random_bytes(16)
    key1 = derive_key(password, salt)
    key2 = derive_key(password, salt)
    assert key1 == key2

def test_derive_key_uniqueness():
    password = "password123"
    salt1 = random_bytes(16)
    salt2 = random_bytes(16)
    key1 = derive_key(password, salt1)
    key2 = derive_key(password, salt2)
    assert key1 != key2

def test_encrypt_decrypt():
    key = random_bytes(32)
    data = "secret message"
    encrypted = encrypt(data, key)
    
    # Structure check
    parts = encrypted.split(".")
    assert len(parts) == 2
    
    decrypted = decrypt(encrypted, key)
    assert decrypted == data

def test_decrypt_invalid_format():
    key = random_bytes(32)
    with pytest.raises(RedenvError, match="Invalid encrypted string format"):
        decrypt("invalid", key)

def test_decrypt_wrong_key():
    key1 = random_bytes(32)
    key2 = random_bytes(32)
    data = "secret message"
    encrypted = encrypt(data, key1)
    
    with pytest.raises(RedenvError, match="Decryption failed"):
        decrypt(encrypted, key2)

def test_decrypt_tampered_data():
    key = random_bytes(32)
    data = "secret message"
    encrypted = encrypt(data, key)
    
    # Tamper with ciphertext (2nd part)
    parts = encrypted.split(".")
    iv = parts[0]
    ciphertext = hex_to_buffer(parts[1])
    
    # Flip a bit in ciphertext
    tampered_ciphertext = bytearray(ciphertext)
    tampered_ciphertext[0] ^= 1
    
    tampered_encrypted = f"{iv}.{buffer_to_hex(tampered_ciphertext)}"
    
    with pytest.raises(RedenvError, match="Decryption failed"):
        decrypt(tampered_encrypted, key)
