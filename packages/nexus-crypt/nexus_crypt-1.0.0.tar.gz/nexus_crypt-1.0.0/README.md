NEXUS-Crypt

Post-Quantum Cryptographic Suite with Perfect Forward Secrecy

NEXUS-Crypt is a unified cryptographic library combining:
- NEXUS-Cipher: Custom lattice based symmetric encryption
- ML-KEM (Kyber): Key encapsulation for Perfect Forward Secrecy
- ML-DSA (Dilithium): Post-quantum digital signatures
- SHA-256: Cryptographic hashing

Features

Post-quantum secure (resistant to quantum computer attacks)  
Perfect Forward Secrecy (PFS) via ML-KEM  
Authenticated encryption with ML-DSA signatures   
Constant time operations (side-channel resistant)  
Easy to use API  

## Installation
```bash
pip install nexus-crypt
```

## Quick Start
```python
from nexus import NEXUS

nexus = NEXUS(key_size=256)

kem_pk, kem_sk = nexus.generate_kem_keypair()
sign_pk, sign_sk = nexus.generate_signing_keypair()

ciphertext, shared_secret = nexus.establish_session(kem_pk)

message = b"Secret data"
package = nexus.encrypt_and_sign(message, sign_sk)

plaintext = nexus.verify_and_decrypt(package, sign_pk)
```

## Security Properties

- Quantum Resistance: Based on lattice problems (LWE, NTRU)
- Key Sizes: 256, 384, or 512 bits
- Block Size: 512 bits (64 bytes)
- Rounds: 20-24 depending on key size

## Use Cases

- Automotive CAN bus encryption
- OTA firmware updates
- V2X communication
- IoT device security
- Secure messaging

## License

MIT License

## Author

Harshith Madhavaram 
MS Cybersecurity '2027
Northeastern University, Boston
```

---

## `.gitignore`**
```
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
.pytest_cache/
.coverage
htmlcov/
.env
venv/
ENV/