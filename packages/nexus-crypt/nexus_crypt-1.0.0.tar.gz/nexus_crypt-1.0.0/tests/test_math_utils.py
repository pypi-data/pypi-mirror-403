"""Unit tests for mathematical utilities"""

import pytest
import secrets
from nexus.math_utils import (
    rol, ror, bytes_to_words, words_to_bytes,
    gf128_multiply, generate_lwe_sbox, generate_ntru_permutation,
    hkdf_sha256, ensure_bijection
)
from nexus.constants import SBOX_SIZE, NTRU_N

class TestRotationOperations:
    """Test rotation operations"""
    
    def test_rotate_left(self):
        """Test left rotation"""
        value = 0b1010
        rotated = rol(value, 1, bits=4)
        assert rotated == 0b0101
    
    def test_rotate_right(self):
        """Test right rotation"""
        value = 0b1010
        rotated = ror(value, 1, bits=4)
        assert rotated == 0b0101
    
    def test_rotate_left_wraparound(self):
        """Test left rotation with wraparound"""
        value = 0b1000
        rotated = rol(value, 1, bits=4)
        assert rotated == 0b0001
    
    def test_rotate_128bit(self):
        """Test 128-bit rotation"""
        value = (1 << 127)  # MSB set
        rotated = rol(value, 1, bits=128)
        assert rotated == 1  # Wrapped to LSB
    
    def test_rotation_identity(self):
        """Test that rotating by full width returns original"""
        value = 0xABCD
        rotated = rol(value, 128, bits=128)
        assert rotated == value


class TestWordConversion:
    """Test byte/word conversion"""
    
    def test_bytes_to_words(self):
        """Test converting bytes to 128-bit words"""
        data = b'\x00' * 16 + b'\xFF' * 16
        words = bytes_to_words(data)
        
        assert len(words) == 2
        assert words[0] == 0
        assert words[1] == (1 << 128) - 1
    
    def test_words_to_bytes(self):
        """Test converting words back to bytes"""
        words = [0xABCD, 0x1234]
        data = words_to_bytes(words)
        
        assert len(data) == 32
        assert bytes_to_words(data) == words
    
    def test_round_trip_conversion(self):
        """Test round-trip byte <-> word conversion"""
        original = secrets.token_bytes(64)
        words = bytes_to_words(original)
        recovered = words_to_bytes(words)
        
        assert recovered == original


class TestGaloisFieldArithmetic:
    """Test GF(2^128) operations"""
    
    def test_gf128_multiply_zero(self):
        """Test multiplication by zero"""
        a = 0xFFFFFFFF
        result = gf128_multiply(a, 0)
        assert result == 0
    
    def test_gf128_multiply_one(self):
        """Test multiplication by one (identity)"""
        a = 0x123456789ABCDEF
        result = gf128_multiply(a, 1)
        assert result == a
    
    def test_gf128_multiply_commutativity(self):
        """Test that multiplication is commutative"""
        a = 0xABCD1234
        b = 0x5678EF12   # Random value
        
        result1 = gf128_multiply(a, b)
        result2 = gf128_multiply(b, a)
        
        assert result1 == result2
    
    def test_gf128_multiply_produces_valid_result(self):
        """Test that result fits in 128 bits"""
        a = (1 << 127)  # Large value
        b = (1 << 127)
        
        result = gf128_multiply(a, b)
        assert result < (1 << 128)


class TestLWESbox:
    """Test LWE S-box generation"""
    
    def test_sbox_correct_size(self):
        """Test S-box has correct size"""
        key = secrets.token_bytes(32)
        sbox = generate_lwe_sbox(key, 0, 0)
        
        assert len(sbox) == SBOX_SIZE
    
    def test_sbox_is_bijection(self):
        """Test S-box is a valid permutation"""
        key = secrets.token_bytes(32)
        sbox = generate_lwe_sbox(key, 0, 0)
        
        # All values should be unique
        assert len(set(sbox)) == SBOX_SIZE
        # All values in range [0, 255]
        assert all(0 <= v < 256 for v in sbox)
    
    def test_sbox_deterministic(self):
        """Test S-box generation is deterministic"""
        key = secrets.token_bytes(32)
        
        sbox1 = generate_lwe_sbox(key, 0, 0)
        sbox2 = generate_lwe_sbox(key, 0, 0)
        
        assert sbox1 == sbox2
    
    def test_different_keys_produce_different_sboxes(self):
        """Test different keys produce different S-boxes"""
        key1 = secrets.token_bytes(32)
        key2 = secrets.token_bytes(32)
        
        sbox1 = generate_lwe_sbox(key1, 0, 0)
        sbox2 = generate_lwe_sbox(key2, 0, 0)
        
        assert sbox1 != sbox2
    
    def test_different_counters_produce_different_sboxes(self):
        """Test different counters regenerate S-boxes"""
        key = secrets.token_bytes(32)
        
        sbox1 = generate_lwe_sbox(key, 0, 0)
        sbox2 = generate_lwe_sbox(key, 0, 1)
        
        assert sbox1 != sbox2
    
    def test_ensure_bijection_fixes_duplicates(self):
        """Test bijection enforcement"""
        # Create list with duplicates
        sbox = list(range(256))
        sbox[5] = sbox[10]  # Create duplicate
        
        fixed = ensure_bijection(sbox)
        
        assert len(set(fixed)) == 256
        assert all(0 <= v < 256 for v in fixed)


class TestNTRUPermutation:
    """Test NTRU permutation generation"""
    
    def test_permutation_correct_size(self):
        """Test permutation has correct size"""
        key = secrets.token_bytes(32)
        perm = generate_ntru_permutation(key, 0)
        
        assert len(perm) == NTRU_N
    
    def test_permutation_is_valid(self):
        """Test permutation contains all indices"""
        key = secrets.token_bytes(32)
        perm = generate_ntru_permutation(key, 0)
        
        assert set(perm) == set(range(NTRU_N))
    
    def test_permutation_deterministic(self):
        """Test permutation generation is deterministic"""
        key = secrets.token_bytes(32)
        
        perm1 = generate_ntru_permutation(key, 0)
        perm2 = generate_ntru_permutation(key, 0)
        
        assert perm1 == perm2
    
    def test_different_rounds_produce_different_permutations(self):
        """Test different rounds produce different permutations"""
        key = secrets.token_bytes(32)
        
        perm1 = generate_ntru_permutation(key, 0)
        perm2 = generate_ntru_permutation(key, 1)
        
        assert perm1 != perm2


class TestHKDF:
    """Test HKDF key derivation"""
    
    def test_hkdf_correct_length(self):
        """Test HKDF produces correct length"""
        key = secrets.token_bytes(32)
        derived = hkdf_sha256(key, 64)
        
        assert len(derived) == 64
    
    def test_hkdf_deterministic(self):
        """Test HKDF is deterministic"""
        key = secrets.token_bytes(32)
        
        derived1 = hkdf_sha256(key, 64)
        derived2 = hkdf_sha256(key, 64)
        
        assert derived1 == derived2
    
    def test_hkdf_different_info_produces_different_output(self):
        """Test different info strings produce different outputs"""
        key = secrets.token_bytes(32)
        
        derived1 = hkdf_sha256(key, 64, b"info1")
        derived2 = hkdf_sha256(key, 64, b"info2")
        
        assert derived1 != derived2
    
    def test_hkdf_different_keys_produce_different_output(self):
        """Test different keys produce different outputs"""
        key1 = b'A' * 32
        key2 = b'B' * 32
        
        derived1 = hkdf_sha256(key1, 64)
        derived2 = hkdf_sha256(key2, 64)
        
        assert derived1 != derived2