from typing import Tuple
class MLKEM:

    
    def __init__(self):
        try:
            from pqcrypto.kem.kyber768 import (
                generate_keypair,
                encrypt,
                decrypt
            )
            self.generate_keypair = generate_keypair
            self.encrypt = encrypt
            self.decrypt = decrypt
        except ImportError:
            raise ImportError("pqcrypto not installed")
    
    def keygen(self) -> Tuple[bytes, bytes]:
        return self.generate_keypair()
    
    def encapsulate(self, public_key: bytes) -> Tuple[bytes, bytes]:
        return self.encrypt(public_key)
    
    def decapsulate(self, ciphertext: bytes, secret_key: bytes) -> bytes:
        return self.decrypt(ciphertext, secret_key)