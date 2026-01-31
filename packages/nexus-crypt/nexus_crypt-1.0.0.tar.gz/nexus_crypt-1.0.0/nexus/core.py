import secrets
import hashlib
from typing import List, Tuple
from .math_utils import *
from .constants import *
from .exceptions import *

class NEXUSCipher:

    def __init__(self, key: bytes, key_size: int = 256):
        if key_size not in [256, 384, 512]:
            raise NEXUSError("Key size must be 256, 384, or 512 bits")
        
        expected_len = key_size // 8
        if len(key) != expected_len:
            raise NEXUSError(f"Key must be {expected_len} bytes for {key_size}-bit security")
        
        self.key = key
        self.key_size = key_size
        self.rounds = self._get_rounds()
        self.round_keys = self._derive_round_keys()
        self.sboxes = [generate_lwe_sbox(key, i, 0) for i in range(SBOX_COUNT)]
        self.sbox_counter = 0
        self.bytes_processed = 0
        self.gf_matrices = self._generate_gf_matrices()
    
    def _get_rounds(self) -> int:
        return {256: ROUNDS_256, 384: ROUNDS_384, 512: ROUNDS_512}[self.key_size]
    
    def _derive_round_keys(self) -> List[List[int]]:
        key_material = hkdf_sha256(self.key, self.rounds * 64, b"NEXUS-ROUND-KEYS")
        round_keys = []
        for i in range(self.rounds):
            round_key_bytes = key_material[i*64:(i+1)*64]
            round_key_words = bytes_to_words(round_key_bytes)
            round_keys.append(round_key_words)
        return round_keys
    
    def _generate_gf_matrices(self) -> List[int]:
        matrices = []
        for i in range(NUM_WORDS):
            h = hashlib.sha256()
            h.update(self.key)
            h.update(b"GF-MATRIX")
            h.update(i.to_bytes(1, 'big'))
            matrix_element = int.from_bytes(h.digest()[:16], 'big')
            matrices.append(matrix_element)
        return matrices
    
    def _regenerate_sboxes_if_needed(self):
        if self.bytes_processed >= SBOX_REGEN_BYTES:
            self.sbox_counter += 1
            self.sboxes = [generate_lwe_sbox(self.key, i, self.sbox_counter) for i in range(SBOX_COUNT)]
            self.bytes_processed = 0
    
    def _nexus_round(self, state: List[int], round_num: int) -> List[int]:
        for i in range(NUM_WORDS):
            state[i] = (state[i] + self.round_keys[round_num][i]) & ((1 << 128) - 1)
            state[i] = rol(state[i], PRIME_ROTATIONS[i], 128)
            lattice_const = generate_lattice_constant(round_num, i)
            state[i] ^= lattice_const
        
        state_bytes = bytearray(words_to_bytes(state))
        for byte_idx in range(len(state_bytes)):
            sbox_id = byte_idx % SBOX_COUNT
            state_bytes[byte_idx] = self.sboxes[sbox_id][state_bytes[byte_idx]]
        state = bytes_to_words(bytes(state_bytes))
        
        for i in range(NUM_WORDS):
            state[i] = gf128_multiply(state[i], self.gf_matrices[i])
        
        state_bits = []
        for word in state:
            for bit_pos in range(128):
                state_bits.append((word >> bit_pos) & 1)
        
        ntru_perm = generate_ntru_permutation(self.key, round_num)
        permuted_bits = [state_bits[ntru_perm[i]] for i in range(NTRU_N)]
        
        state = []
        for word_idx in range(NUM_WORDS):
            word = 0
            for bit_idx in range(128):
                bit_pos = word_idx * 128 + bit_idx
                word |= (permuted_bits[bit_pos] << bit_idx)
            state.append(word)
        
        return state
    
    def _generate_keystream(self, nonce: bytes) -> bytes:
        state = [0] * NUM_WORDS
        nonce_extended = nonce + nonce + nonce + nonce
        nonce_words = bytes_to_words(nonce_extended)
        
        for i in range(NUM_WORDS):
            state[i] ^= nonce_words[i]
        
        for round_num in range(self.rounds):
            state = self._nexus_round(state, round_num)
        
        return words_to_bytes(state)
    
    def encrypt_block(self, plaintext: bytes, nonce: bytes) -> bytes:
        if len(plaintext) != BLOCK_SIZE:
            raise NEXUSError(f"Block must be {BLOCK_SIZE} bytes")
        if len(nonce) != NONCE_SIZE:
            raise NEXUSError(f"Nonce must be {NONCE_SIZE} bytes")
        
        keystream = self._generate_keystream(nonce)
        ciphertext = bytes([p ^ k for p, k in zip(plaintext, keystream)])
        self.bytes_processed += BLOCK_SIZE
        self._regenerate_sboxes_if_needed()
        return ciphertext
    
    def decrypt_block(self, ciphertext: bytes, nonce: bytes) -> bytes:
        if len(ciphertext) != BLOCK_SIZE:
            raise NEXUSError(f"Block must be {BLOCK_SIZE} bytes")
        if len(nonce) != NONCE_SIZE:
            raise NEXUSError(f"Nonce must be {NONCE_SIZE} bytes")
        
        keystream = self._generate_keystream(nonce)
        plaintext = bytes([c ^ k for c, k in zip(ciphertext, keystream)])
        self.bytes_processed += BLOCK_SIZE
        self._regenerate_sboxes_if_needed()
        return plaintext
    
    def encrypt(self, plaintext: bytes, nonce: bytes = None) -> Tuple[bytes, bytes]:
        if nonce is None:
            nonce = secrets.token_bytes(NONCE_SIZE)
        
        pad_len = BLOCK_SIZE - (len(plaintext) % BLOCK_SIZE)
        plaintext += bytes([pad_len] * pad_len)
        
        ciphertext = b''
        for i in range(0, len(plaintext), BLOCK_SIZE):
            block = plaintext[i:i+BLOCK_SIZE]
            block_nonce = nonce + i.to_bytes(16, 'big')
            block_nonce = hashlib.sha256(block_nonce).digest()[:NONCE_SIZE]
            encrypted_block = self.encrypt_block(block, block_nonce)
            ciphertext += encrypted_block
        
        return ciphertext, nonce
    
    def decrypt(self, ciphertext: bytes, nonce: bytes) -> bytes:
        if len(ciphertext) % BLOCK_SIZE != 0:
            raise DecryptionError("Invalid ciphertext length")
        
        plaintext = b''
        for i in range(0, len(ciphertext), BLOCK_SIZE):
            block = ciphertext[i:i+BLOCK_SIZE]
            block_nonce = nonce + i.to_bytes(16, 'big')
            block_nonce = hashlib.sha256(block_nonce).digest()[:NONCE_SIZE]
            decrypted_block = self.decrypt_block(block, block_nonce)
            plaintext += decrypted_block
        
        pad_len = plaintext[-1]
        if pad_len <= BLOCK_SIZE and pad_len > 0:
            plaintext = plaintext[:-pad_len]
        
        return plaintext


class NEXUS:

    def __init__(self, key_size: int = 256):
        self.key_size = key_size
        self.cipher = None
        
        try:
            from pqcrypto.kem.ml_kem_768 import generate_keypair as kyber_keygen
            from pqcrypto.kem.ml_kem_768 import encrypt as kyber_encrypt
            from pqcrypto.kem.ml_kem_768 import decrypt as kyber_decrypt
            from pqcrypto.sign.ml_dsa_65 import generate_keypair as dilithium_keygen
            from pqcrypto.sign.ml_dsa_65 import sign as dilithium_sign
            from pqcrypto.sign.ml_dsa_65 import verify as dilithium_verify
            
            self.kyber_keygen = kyber_keygen
            self.kyber_encrypt = kyber_encrypt
            self.kyber_decrypt = kyber_decrypt
            self.dilithium_keygen = dilithium_keygen
            self.dilithium_sign = dilithium_sign
            self.dilithium_verify = dilithium_verify
        except ImportError:
            raise NEXUSError("Please install pqcrypto: pip install pqcrypto")
    
    def generate_kem_keypair(self) -> Tuple[bytes, bytes]:
        public_key, secret_key = self.kyber_keygen()
        return public_key, secret_key
    
    def generate_signing_keypair(self) -> Tuple[bytes, bytes]:
        public_key, secret_key = self.dilithium_keygen()
        return public_key, secret_key
    
    def establish_session(self, peer_public_key: bytes) -> Tuple[bytes, bytes]:
        ciphertext, shared_secret = self.kyber_encrypt(peer_public_key)
        enc_key = hkdf_sha256(shared_secret, self.key_size // 8, b"NEXUS-ENC")
        self.cipher = NEXUSCipher(enc_key, self.key_size)
        return ciphertext, shared_secret
    
    def accept_session(self, ciphertext: bytes, secret_key: bytes) -> bytes:
        shared_secret = self.kyber_decrypt(secret_key, ciphertext)
        enc_key = hkdf_sha256(shared_secret, self.key_size // 8, b"NEXUS-ENC")
        self.cipher = NEXUSCipher(enc_key, self.key_size)
        return shared_secret
    
    def hash(self, data: bytes) -> bytes:
        return hashlib.sha256(data).digest()
    
    def encrypt_and_sign(self, plaintext: bytes, signing_key: bytes) -> dict:
        if self.cipher is None:
            raise NEXUSError("Session not established. Call establish_session first.")
        
        ciphertext, nonce = self.cipher.encrypt(plaintext)
        digest = self.hash(ciphertext)
        signature = self.dilithium_sign(signing_key, digest)
        
        return {'ciphertext': ciphertext, 'nonce': nonce, 'signature': signature}
    
    def verify_and_decrypt(self, package: dict, verify_key: bytes) -> bytes:
        if self.cipher is None:
            raise NEXUSError("Session not established.")
        
        digest = self.hash(package['ciphertext'])
        try:
            is_valid = self.dilithium_verify(verify_key, digest, package['signature'])
            if not is_valid:
                raise SignatureVerificationError("Signature verification failed")
        except Exception as e:
            raise SignatureVerificationError(f"Signature verification failed: {e}")
        
        plaintext = self.cipher.decrypt(package['ciphertext'], package['nonce'])
        return plaintext