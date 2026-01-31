"""Basic usage example for NEXUS-Crypt"""

from nexus import NEXUS

def main():
    print("=== NEXUS-Crypt Demo ===\n")
    
   
    nexus = NEXUS(key_size=256)
    
  
    print("1. Generating keys...")
    alice_kem_pk, alice_kem_sk = nexus.generate_kem_keypair()
    alice_sign_pk, alice_sign_sk = nexus.generate_signing_keypair()
    
    bob_kem_pk, bob_kem_sk = nexus.generate_kem_keypair()
    bob_sign_pk, bob_sign_sk = nexus.generate_signing_keypair()
    print("Keys generated\n")
    

    print("2. Alice establishing session with Bob...")
    alice_nexus = NEXUS(key_size=256)
    kem_ciphertext, alice_shared = alice_nexus.establish_session(bob_kem_pk)
    print(f"Session established (shared secret: {alice_shared[:8].hex()}...)\n")
    
    print("3. Bob accepting session...")
    bob_nexus = NEXUS(key_size=256)
    bob_shared = bob_nexus.accept_session(kem_ciphertext, bob_kem_sk)
    print(f" Session accepted (shared secret: {bob_shared[:8].hex()}...)\n")
 
    assert alice_shared == bob_shared, "Shared secrets don't match!"
    
   
    print("4. Alice encrypting and signing message...")
    message = b"Hello Bob! This is a secure message using NEXUS-Crypt with PFS!"
    package = alice_nexus.encrypt_and_sign(message, alice_sign_sk)
    print(f" Message encrypted ({len(package['ciphertext'])} bytes)")
    print(f"Signature generated ({len(package['signature'])} bytes)\n")
    
    print("5. Bob verifying and decrypting...")
    decrypted = bob_nexus.verify_and_decrypt(package, alice_sign_pk)
    print(f" Signature verified")
    print(f" Message decrypted: {decrypted.decode()}\n")

    assert decrypted == message, "Decryption failed!"
    
    print("=== All tests passed! ===")

if __name__ == "__main__":
    main()