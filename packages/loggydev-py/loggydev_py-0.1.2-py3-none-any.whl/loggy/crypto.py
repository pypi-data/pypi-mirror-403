"""
Hybrid encryption for log payloads.
Uses AES-256-GCM for data encryption and RSA-OAEP for key encryption.
"""

import base64
import json
import os
from typing import Any, Dict

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def encrypt_payload(data: Any, public_key_pem: str) -> Dict[str, str]:
    """
    Encrypts data using hybrid encryption (AES-256-GCM + RSA-OAEP).

    Args:
        data: The data to encrypt (will be JSON serialized)
        public_key_pem: The server's RSA public key in PEM format

    Returns:
        Encrypted payload with all components needed for decryption:
        - encryptedKey: RSA-encrypted AES key (base64)
        - iv: AES initialization vector (base64)
        - authTag: AES-GCM auth tag (base64)
        - data: AES-encrypted data (base64)
    """
    # Generate random AES-256 key and IV
    aes_key = os.urandom(32)  # 256 bits
    iv = os.urandom(12)  # 96 bits for GCM

    # Encrypt data with AES-256-GCM
    aesgcm = AESGCM(aes_key)
    json_data = json.dumps(data).encode("utf-8")
    ciphertext_with_tag = aesgcm.encrypt(iv, json_data, None)

    # AES-GCM appends the auth tag to the ciphertext
    # The tag is the last 16 bytes
    ciphertext = ciphertext_with_tag[:-16]
    auth_tag = ciphertext_with_tag[-16:]

    # Load the public key
    public_key = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))

    # Encrypt AES key with RSA-OAEP
    encrypted_key = public_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    return {
        "encryptedKey": base64.b64encode(encrypted_key).decode("utf-8"),
        "iv": base64.b64encode(iv).decode("utf-8"),
        "authTag": base64.b64encode(auth_tag).decode("utf-8"),
        "data": base64.b64encode(ciphertext).decode("utf-8"),
    }
