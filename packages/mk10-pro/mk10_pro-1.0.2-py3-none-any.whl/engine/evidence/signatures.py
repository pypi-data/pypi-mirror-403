# SPDX-License-Identifier: MIT
"""Cryptographic signatures for evidence."""

from typing import Optional
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key,
    load_pem_public_key,
    Encoding,
    PublicFormat,
    PrivateFormat,
    NoEncryption,
)
from cryptography.hazmat.backends import default_backend


class Signer:
    """Sign evidence with private key."""
    
    def __init__(self, private_key_pem: Optional[bytes] = None):
        if private_key_pem:
            self.private_key = load_pem_private_key(
                private_key_pem,
                password=None,
                backend=default_backend(),
            )
        else:
            # Generate new key for testing
            self.private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend(),
            )
    
    def sign(self, data: bytes) -> dict:
        """
        Sign data.
        
        Returns:
            Dictionary with signature and public key
        """
        signature = self.private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )
        
        public_key = self.private_key.public_key()
        public_key_pem = public_key.public_bytes(
            Encoding.PEM,
            PublicFormat.SubjectPublicKeyInfo,
        )
        
        return {
            "signature": signature.hex(),
            "algorithm": "RSA-PSS-SHA256",
            "public_key": public_key_pem.decode("utf-8"),
        }
    
    def get_public_key_pem(self) -> str:
        """Get public key in PEM format."""
        public_key = self.private_key.public_key()
        return public_key.public_bytes(
            Encoding.PEM,
            PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")


class Verifier:
    """Verify signatures."""
    
    @staticmethod
    def verify(data: bytes, signature_info: dict) -> bool:
        """
        Verify signature.
        
        Args:
            data: Original data
            signature_info: Dictionary with signature, algorithm, public_key
            
        Returns:
            True if signature is valid
        """
        try:
            public_key = load_pem_public_key(
                signature_info["public_key"].encode("utf-8"),
                backend=default_backend(),
            )
            
            signature_bytes = bytes.fromhex(signature_info["signature"])
            
            public_key.verify(
                signature_bytes,
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )
            return True
        except Exception:
            return False

