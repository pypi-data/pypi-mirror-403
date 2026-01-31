class NEXUSError(Exception):
    pass

class DecryptionError(NEXUSError):
    pass

class SignatureVerificationError(NEXUSError):
    pass

class KeyGenerationError(NEXUSError):
    pass