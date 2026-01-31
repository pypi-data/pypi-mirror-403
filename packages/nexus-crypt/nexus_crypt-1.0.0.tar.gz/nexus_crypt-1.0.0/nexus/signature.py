class MLDSA:
    def __init__(self):
        try:
            from pqcrypto.sign.dilithium3 import (
                generate_keypair,
                sign,
                verify
            )
            self.generate_keypair = generate_keypair
            self.sign = sign
            self.verify = verify
        except ImportError:
            raise ImportError("pqcrypto not installed")
    
    def keygen(self):
        return self.generate_keypair()
    
    def sign_message(self, message: bytes, secret_key: bytes) -> bytes:

        return self.sign(message, secret_key)
    def verify_signature(self, signature: bytes, message: bytes, public_key: bytes) -> bool:
        try:
            self.verify(signature, message, public_key)
            return True
        except:
            return False