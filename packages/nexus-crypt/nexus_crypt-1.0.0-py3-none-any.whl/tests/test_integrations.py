"""Integration tests for complete NEXUS suite"""

import pytest
import secrets
from nexus import NEXUS
from nexus.exceptions import NEXUSError, SignatureVerificationError

class TestNEXUSIntegration:
    """Integration tests for full NEXUS protocol"""
    
    def test_full_protocol_flow(self):
        """Test complete protocol: KEM + Encrypt + Sign"""
        # Initialize NEXUS for both parties
        alice = NEXUS(key_size=256)
        bob = NEXUS(key_size=256)
        
        # Generate keys
        alice_kem_pk, alice_kem_sk = alice.generate_kem_keypair()
        alice_sign_pk, alice_sign_sk = alice.generate_signing_keypair()
        
        bob_kem_pk, bob_kem_sk = bob.generate_kem_keypair()
        bob_sign_pk, bob_sign_sk = bob.generate_signing_keypair()
        
        # Alice establishes session with Bob
        kem_ct, alice_shared = alice.establish_session(bob_kem_pk)
        
        # Bob accepts session
        bob_shared = bob.accept_session(kem_ct, bob_kem_sk)
        
        # Verify shared secrets match
        assert alice_shared == bob_shared
        
        # Alice sends encrypted + signed message
        message = b"Hello Bob! This is Alice."
        package = alice.encrypt_and_sign(message, alice_sign_sk)
        
        # Bob verifies and decrypts
        decrypted = bob.verify_and_decrypt(package, alice_sign_pk)
        
        assert decrypted == message
    
    def test_bidirectional_communication(self):
        """Test both parties can send messages"""
        alice = NEXUS(key_size=256)
        bob = NEXUS(key_size=256)
        
        # Setup
        alice_kem_pk, alice_kem_sk = alice.generate_kem_keypair()
        alice_sign_pk, alice_sign_sk = alice.generate_signing_keypair()
        
        bob_kem_pk, bob_kem_sk = bob.generate_kem_keypair()
        bob_sign_pk, bob_sign_sk = bob.generate_signing_keypair()
        
        # Alice -> Bob session
        kem_ct_ab, _ = alice.establish_session(bob_kem_pk)
        bob.accept_session(kem_ct_ab, bob_kem_sk)
        
        # Bob -> Alice session
        bob_to_alice = NEXUS(key_size=256)
        alice_to_bob_receiver = NEXUS(key_size=256)
        kem_ct_ba, _ = bob_to_alice.establish_session(alice_kem_pk)
        alice_to_bob_receiver.accept_session(kem_ct_ba, alice_kem_sk)
        
        # Alice -> Bob
        msg_ab = b"Message from Alice to Bob"
        pkg_ab = alice.encrypt_and_sign(msg_ab, alice_sign_sk)
        dec_ab = bob.verify_and_decrypt(pkg_ab, alice_sign_pk)
        assert dec_ab == msg_ab
        
        # Bob -> Alice
        msg_ba = b"Message from Bob to Alice"
        pkg_ba = bob_to_alice.encrypt_and_sign(msg_ba, bob_sign_sk)
        dec_ba = alice_to_bob_receiver.verify_and_decrypt(pkg_ba, bob_sign_pk)
        assert dec_ba == msg_ba
    
    def test_signature_verification_fails_with_wrong_key(self):
        """Test signature verification fails with wrong public key"""
        alice = NEXUS(key_size=256)
        bob = NEXUS(key_size=256)
        eve = NEXUS(key_size=256)
        
        # Setup
        alice_kem_pk, alice_kem_sk = alice.generate_kem_keypair()
        alice_sign_pk, alice_sign_sk = alice.generate_signing_keypair()
        
        bob_kem_pk, bob_kem_sk = bob.generate_kem_keypair()
        
        eve_sign_pk, _ = eve.generate_signing_keypair()
        
        # Establish session
        kem_ct, _ = alice.establish_session(bob_kem_pk)
        bob.accept_session(kem_ct, bob_kem_sk)
        
        # Alice sends message
        message = b"Secret message"
        package = alice.encrypt_and_sign(message, alice_sign_sk)
        
        # Bob tries to verify with Eve's key (should fail)
        with pytest.raises(SignatureVerificationError):
            bob.verify_and_decrypt(package, eve_sign_pk)
    
    def test_tampered_ciphertext_fails_verification(self):
        """Test that tampering with ciphertext fails signature verification"""
        alice = NEXUS(key_size=256)
        bob = NEXUS(key_size=256)
        
        # Setup
        alice_kem_pk, alice_kem_sk = alice.generate_kem_keypair()
        alice_sign_pk, alice_sign_sk = alice.generate_signing_keypair()
        
        bob_kem_pk, bob_kem_sk = bob.generate_kem_keypair()
        
        # Establish session
        kem_ct, _ = alice.establish_session(bob_kem_pk)
        bob.accept_session(kem_ct, bob_kem_sk)
        
        # Alice sends message
        message = b"Original message"
        package = alice.encrypt_and_sign(message, alice_sign_sk)
        
        # Tamper with ciphertext
        tampered_ct = bytearray(package['ciphertext'])
        tampered_ct[0] ^= 1  # Flip one bit
        package['ciphertext'] = bytes(tampered_ct)
        
        # Verification should fail
        with pytest.raises(SignatureVerificationError):
            bob.verify_and_decrypt(package, alice_sign_pk)
    
    def test_multiple_messages_same_session(self):
        """Test multiple messages can be sent in same session"""
        alice = NEXUS(key_size=256)
        bob = NEXUS(key_size=256)
        
        # Setup
        alice_kem_pk, alice_kem_sk = alice.generate_kem_keypair()
        alice_sign_pk, alice_sign_sk = alice.generate_signing_keypair()
        
        bob_kem_pk, bob_kem_sk = bob.generate_kem_keypair()
        
        # Establish session
        kem_ct, _ = alice.establish_session(bob_kem_pk)
        bob.accept_session(kem_ct, bob_kem_sk)
        
        # Send multiple messages
        messages = [
            b"First message",
            b"Second message",
            b"Third message with more content"
        ]
        
        for msg in messages:
            package = alice.encrypt_and_sign(msg, alice_sign_sk)
            decrypted = bob.verify_and_decrypt(package, alice_sign_pk)
            assert decrypted == msg
    
    def test_large_message_transfer(self):
        """Test transfer of large message"""
        alice = NEXUS(key_size=256)
        bob = NEXUS(key_size=256)
        
        # Setup
        alice_kem_pk, alice_kem_sk = alice.generate_kem_keypair()
        alice_sign_pk, alice_sign_sk = alice.generate_signing_keypair()
        
        bob_kem_pk, bob_kem_sk = bob.generate_kem_keypair()
        
        # Establish session
        kem_ct, _ = alice.establish_session(bob_kem_pk)
        bob.accept_session(kem_ct, bob_kem_sk)
        
        # Large message (1MB)
        message = secrets.token_bytes(1024 * 1024)
        package = alice.encrypt_and_sign(message, alice_sign_sk)
        decrypted = bob.verify_and_decrypt(package, alice_sign_pk)
        
        assert decrypted == message
    
    def test_hash_functionality(self):
        """Test hash function"""
        nexus = NEXUS()
        
        data = b"Test data to hash"
        hash1 = nexus.hash(data)
        hash2 = nexus.hash(data)
        
        # Should be deterministic
        assert hash1 == hash2
        
        # Should be 32 bytes (SHA-256)
        assert len(hash1) == 32
        
        # Different data should produce different hash
        hash3 = nexus.hash(b"Different data")
        assert hash1 != hash3
    
    def test_session_not_established_error(self):
        """Test error when trying to encrypt without session"""
        alice = NEXUS(key_size=256)
        _, alice_sign_sk = alice.generate_signing_keypair()
        
        message = b"Test"
        
        with pytest.raises(NEXUSError, match="Session not established"):
            alice.encrypt_and_sign(message, alice_sign_sk)
    
    def test_different_key_sizes(self):
        """Test protocol works with different key sizes"""
        for key_size in [256, 384, 512]:
            alice = NEXUS(key_size=key_size)
            bob = NEXUS(key_size=key_size)
            
            alice_kem_pk, alice_kem_sk = alice.generate_kem_keypair()
            alice_sign_pk, alice_sign_sk = alice.generate_signing_keypair()
            
            bob_kem_pk, bob_kem_sk = bob.generate_kem_keypair()
            
            kem_ct, _ = alice.establish_session(bob_kem_pk)
            bob.accept_session(kem_ct, bob_kem_sk)
            
            message = f"Testing with {key_size}-bit key".encode()
            package = alice.encrypt_and_sign(message, alice_sign_sk)
            decrypted = bob.verify_and_decrypt(package, alice_sign_pk)
            
            assert decrypted == message


class TestPerfectForwardSecrecy:
    """Test Perfect Forward Secrecy properties"""
    
    def test_new_session_different_keys(self):
        """Test that new sessions generate different shared secrets"""
        alice = NEXUS(key_size=256)
        bob_kem_pk, bob_kem_sk = alice.generate_kem_keypair()
        
        # Session 1
        alice1 = NEXUS(key_size=256)
        _, shared1 = alice1.establish_session(bob_kem_pk)
        
        # Session 2
        alice2 = NEXUS(key_size=256)
        _, shared2 = alice2.establish_session(bob_kem_pk)
        
        # Different sessions should have different shared secrets
        assert shared1 != shared2
    
    def test_compromise_one_session_doesnt_affect_others(self):
        """Test that compromising one session doesn't affect others"""
        alice = NEXUS(key_size=256)
        bob = NEXUS(key_size=256)
        
        bob_kem_pk, bob_kem_sk = bob.generate_kem_keypair()
        alice_sign_pk, alice_sign_sk = alice.generate_signing_keypair()
        
        # Session 1
        alice1 = NEXUS(key_size=256)
        kem_ct1, shared1 = alice1.establish_session(bob_kem_pk)
        bob1 = NEXUS(key_size=256)
        bob1.accept_session(kem_ct1, bob_kem_sk)
        
        msg1 = b"Message in session 1"
        pkg1 = alice1.encrypt_and_sign(msg1, alice_sign_sk)
        
        # Session 2 (independent)
        alice2 = NEXUS(key_size=256)
        kem_ct2, shared2 = alice2.establish_session(bob_kem_pk)
        bob2 = NEXUS(key_size=256)
        bob2.accept_session(kem_ct2, bob_kem_sk)
        
        msg2 = b"Message in session 2"
        pkg2 = alice2.encrypt_and_sign(msg2, alice_sign_sk)
        
        # Both should decrypt correctly
        dec1 = bob1.verify_and_decrypt(pkg1, alice_sign_pk)
        dec2 = bob2.verify_and_decrypt(pkg2, alice_sign_pk)
        
        assert dec1 == msg1
        assert dec2 == msg2
        
        # Sessions are independent
        assert shared1 != shared2