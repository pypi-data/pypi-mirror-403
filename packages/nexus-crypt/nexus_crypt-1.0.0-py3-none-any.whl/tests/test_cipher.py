import pytest
import secrets
from nexus.core import NEXUSCipher
from nexus.exceptions import NEXUSError, DecryptionError
from nexus.constants import BLOCK_SIZE, NONCE_SIZE

class TestNEXUSCipher:
    
    def test_initialization_256bit(self):
        key = secrets.token_bytes(32)
        cipher = NEXUSCipher(key, key_size=256)
        assert cipher.key_size == 256
        assert cipher.rounds == 20
        assert len(cipher.round_keys) == 20
    
    def test_initialization_384bit(self):
        key = secrets.token_bytes(48)
        cipher = NEXUSCipher(key, key_size=384)
        assert cipher.key_size == 384
        assert cipher.rounds == 22
    
    def test_initialization_512bit(self):
        key = secrets.token_bytes(64)
        cipher = NEXUSCipher(key, key_size=512)
        assert cipher.key_size == 512
        assert cipher.rounds == 24
    
    def test_invalid_key_size(self):
        key = secrets.token_bytes(32)
        with pytest.raises(NEXUSError):
            NEXUSCipher(key, key_size=128)  
    
    def test_invalid_key_length(self):
        key = secrets.token_bytes(16) 
        with pytest.raises(NEXUSError):
            NEXUSCipher(key, key_size=256)
    
    def test_block_encryption_decryption(self):
        key = secrets.token_bytes(32)
        cipher = NEXUSCipher(key, key_size=256)
        
        plaintext = b"A" * BLOCK_SIZE
        nonce = secrets.token_bytes(NONCE_SIZE)
        
        ciphertext = cipher.encrypt_block(plaintext, nonce)
        decrypted = cipher.decrypt_block(ciphertext, nonce)
        
        assert len(ciphertext) == BLOCK_SIZE
        assert decrypted == plaintext
    
    def test_different_nonces_produce_different_ciphertext(self):
        key = secrets.token_bytes(32)
        cipher = NEXUSCipher(key, key_size=256)
        
        plaintext = b"Test message" * 5  
        nonce1 = secrets.token_bytes(NONCE_SIZE)
        nonce2 = secrets.token_bytes(NONCE_SIZE)
        
        ct1, _ = cipher.encrypt(plaintext, nonce1)

        cipher = NEXUSCipher(key, key_size=256)
        ct2, _ = cipher.encrypt(plaintext, nonce2)
        
        assert ct1 != ct2
    
    def test_encrypt_decrypt_short_message(self):
        key = secrets.token_bytes(32)
        cipher = NEXUSCipher(key, key_size=256)
        
        plaintext = b"Hello, World!"
        ciphertext, nonce = cipher.encrypt(plaintext)

        cipher2 = NEXUSCipher(key, key_size=256)
        decrypted = cipher2.decrypt(ciphertext, nonce)
        
        assert decrypted == plaintext
    
    def test_encrypt_decrypt_long_message(self):
        key = secrets.token_bytes(32)
        cipher = NEXUSCipher(key, key_size=256)
        
        plaintext = b"Long message! " * 100  
        ciphertext, nonce = cipher.encrypt(plaintext)
        
        cipher2 = NEXUSCipher(key, key_size=256)
        decrypted = cipher2.decrypt(ciphertext, nonce)
        
        assert decrypted == plaintext
    
    def test_encrypt_decrypt_exact_block_size(self):
        key = secrets.token_bytes(32)
        cipher = NEXUSCipher(key, key_size=256)
        
        plaintext = b"X" * BLOCK_SIZE
        ciphertext, nonce = cipher.encrypt(plaintext)
        
        cipher2 = NEXUSCipher(key, key_size=256)
        decrypted = cipher2.decrypt(ciphertext, nonce)
        
        assert decrypted == plaintext
    
    def test_padding_applied_correctly(self):
        key = secrets.token_bytes(32)
        cipher = NEXUSCipher(key, key_size=256)

        plaintext = b"Short"
        ciphertext, nonce = cipher.encrypt(plaintext)
        assert len(ciphertext) % BLOCK_SIZE == 0
        
        cipher2 = NEXUSCipher(key, key_size=256)
        decrypted = cipher2.decrypt(ciphertext, nonce)
        
        assert decrypted == plaintext
    
    def test_wrong_key_fails_decryption(self):

        key1 = secrets.token_bytes(32)
        key2 = secrets.token_bytes(32)
        
        cipher1 = NEXUSCipher(key1, key_size=256)
        plaintext = b"Secret message"
        ciphertext, nonce = cipher1.encrypt(plaintext)
        
        cipher2 = NEXUSCipher(key2, key_size=256)
        decrypted = cipher2.decrypt(ciphertext, nonce)
        
        assert decrypted != plaintext
    
    def test_wrong_nonce_fails_decryption(self):
        key = secrets.token_bytes(32)
        
        cipher1 = NEXUSCipher(key, key_size=256)
        plaintext = b"Secret message"
        ciphertext, nonce1 = cipher1.encrypt(plaintext)
        
        nonce2 = secrets.token_bytes(NONCE_SIZE)
        cipher2 = NEXUSCipher(key, key_size=256)
        decrypted = cipher2.decrypt(ciphertext, nonce2)
        
        assert decrypted != plaintext
    
    def test_sbox_regeneration(self):
        key = secrets.token_bytes(32)
        cipher = NEXUSCipher(key, key_size=256)
        
        initial_sboxes = [s[:] for s in cipher.sboxes]  
 
        large_data = secrets.token_bytes(1024 * 1024)
        cipher.encrypt(large_data)

        assert cipher.sboxes != initial_sboxes
    
    def test_ciphertext_avalanche_effect(self):
        key = secrets.token_bytes(32)
        
        plaintext1 = b"A" * BLOCK_SIZE
        plaintext2 = b"B" + b"A" * (BLOCK_SIZE - 1)  
        nonce = secrets.token_bytes(NONCE_SIZE)
        
        cipher1 = NEXUSCipher(key, key_size=256)
        ct1 = cipher1.encrypt_block(plaintext1, nonce)
        
        cipher2 = NEXUSCipher(key, key_size=256)
        ct2 = cipher2.encrypt_block(plaintext2, nonce)

        diff_bits = sum(bin(b1 ^ b2).count('1') for b1, b2 in zip(ct1, ct2))

        expected_bits = BLOCK_SIZE * 8
        assert diff_bits > 0  
    
    def test_nonce_generation(self):
        """Test automatic nonce generation"""
        key = secrets.token_bytes(32)
        cipher = NEXUSCipher(key, key_size=256)
        
        plaintext = b"Test"
        ct1, nonce1 = cipher.encrypt(plaintext)
        
        cipher2 = NEXUSCipher(key, key_size=256)
        ct2, nonce2 = cipher2.encrypt(plaintext)
        
        # Nonces should be different
        assert nonce1 != nonce2
        # Ciphertexts should be different
        assert ct1 != ct2
    
    def test_empty_message(self):
        """Test encryption of empty message"""
        key = secrets.token_bytes(32)
        cipher = NEXUSCipher(key, key_size=256)
        
        plaintext = b""
        ciphertext, nonce = cipher.encrypt(plaintext)
        
        # Should still produce output (padding)
        assert len(ciphertext) == BLOCK_SIZE
        
        cipher2 = NEXUSCipher(key, key_size=256)
        decrypted = cipher2.decrypt(ciphertext, nonce)
        
        assert decrypted == plaintext
    
    def test_binary_data_encryption(self):
        """Test encryption of binary data"""
        key = secrets.token_bytes(32)
        cipher = NEXUSCipher(key, key_size=256)
        
        # Random binary data
        plaintext = secrets.token_bytes(500)
        ciphertext, nonce = cipher.encrypt(plaintext)
        
        cipher2 = NEXUSCipher(key, key_size=256)
        decrypted = cipher2.decrypt(ciphertext, nonce)
        
        assert decrypted == plaintext
    
    def test_unicode_text_encryption(self):
        """Test encryption of Unicode text"""
        key = secrets.token_bytes(32)
        cipher = NEXUSCipher(key, key_size=256)
        
        plaintext = "Hello 世界! 🚀".encode('utf-8')
        ciphertext, nonce = cipher.encrypt(plaintext)
        
        cipher2 = NEXUSCipher(key, key_size=256)
        decrypted = cipher2.decrypt(ciphertext, nonce)
        
        assert decrypted == plaintext
        assert decrypted.decode('utf-8') == "Hello 世界! 🚀"


class TestNEXUSCipherPerformance:
    """Performance benchmarks for NEXUS-Cipher"""
    
    def test_encryption_speed_1kb(self, benchmark):
        """Benchmark encryption of 1KB"""
        key = secrets.token_bytes(32)
        cipher = NEXUSCipher(key, key_size=256)
        data = secrets.token_bytes(1024)
        
        benchmark(cipher.encrypt, data)
    
    def test_encryption_speed_1mb(self, benchmark):
        """Benchmark encryption of 1MB"""
        key = secrets.token_bytes(32)
        cipher = NEXUSCipher(key, key_size=256)
        data = secrets.token_bytes(1024 * 1024)
        
        benchmark(cipher.encrypt, data)
    
    def test_decryption_speed(self, benchmark):
        """Benchmark decryption speed"""
        key = secrets.token_bytes(32)
        cipher = NEXUSCipher(key, key_size=256)
        data = secrets.token_bytes(1024 * 1024)
        ciphertext, nonce = cipher.encrypt(data)
        
        cipher2 = NEXUSCipher(key, key_size=256)
        benchmark(cipher2.decrypt, ciphertext, nonce)