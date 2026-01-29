import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from .errors import RedenvError

# --- Configuration ---
IV_LENGTH = 12
KEY_LENGTH = 32 # 256 bits = 32 bytes
PBKDF2_ITERATIONS = 310000
SALT_LENGTH = 16

def buffer_to_hex(buffer: bytes) -> str:
    return buffer.hex()

def hex_to_buffer(hex_str: str) -> bytes:
    return bytes.fromhex(hex_str)

def random_bytes(length: int = 32) -> bytes:
    return os.urandom(length)

def generate_salt() -> bytes:
    return random_bytes(SALT_LENGTH)

def derive_key(password: str, salt: bytes) -> bytes:
    """
    Derives an encryption key from a password and salt using PBKDF2.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_LENGTH,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return kdf.derive(password.encode('utf-8'))

def encrypt(data: str, key: bytes) -> str:
    """
    Encrypts data using AES-256-GCM.
    Returns a string containing the iv and the ciphertext, separated by a dot.
    """
    iv = os.urandom(IV_LENGTH)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(iv, data.encode('utf-8'), None)
    
    return f"{buffer_to_hex(iv)}.{buffer_to_hex(ciphertext)}"

def decrypt(encrypted_string: str, key: bytes) -> str:
    """
    Decrypts data that was encrypted with the `encrypt` function.
    """
    if not encrypted_string:
        raise RedenvError("Encrypted string cannot be empty.", "UNKNOWN_ERROR")

    parts = encrypted_string.split(".")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise RedenvError("Invalid encrypted string format.", "UNKNOWN_ERROR")

    try:
        iv = hex_to_buffer(parts[0])
        ciphertext = hex_to_buffer(parts[1])
        
        aesgcm = AESGCM(key)
        decrypted_data = aesgcm.decrypt(iv, ciphertext, None)
        
        return decrypted_data.decode('utf-8')
    except Exception:
        raise RedenvError(
            "Decryption failed. This likely means an incorrect password was used or the data is corrupted.",
            "DECRYPTION_FAILED"
        )
