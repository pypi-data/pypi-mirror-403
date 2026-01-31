import secrets
import hashlib
import numpy as np
from typing import List, Tuple
from .constants import *

def rol(value: int, shift: int, bits: int = 128) -> int:
    shift %= bits
    mask = (1 << bits) - 1
    return ((value << shift) | (value >> (bits - shift))) & mask

def ror(value: int, shift: int, bits: int = 128) -> int:
    return rol(value, bits - shift, bits)

def bytes_to_words(data: bytes) -> List[int]:
    words = []
    for i in range(0, len(data), 16):
        word = int.from_bytes(data[i:i+16], 'big')
        words.append(word)
    return words

def words_to_bytes(words: List[int]) -> bytes:
    result = b''
    for word in words:
        result += word.to_bytes(16, 'big')
    return result

def gf128_multiply(a: int, b: int) -> int:
    result = 0
    for i in range(128):
        if b & (1 << i):
            result ^= a
        
        carry = a >> 127
        a = (a << 1) & ((1 << 128) - 1)
        if carry:
            a ^= GF128_POLY
    
    return result

def gaussian_sample(sigma: float) -> int:
    return int(np.random.normal(0, sigma))

def generate_lwe_matrix(seed: bytes, size: int) -> List[List[int]]:
    rng = np.random.RandomState(int.from_bytes(seed[:4], 'big'))
    return [[int(rng.randint(0, LWE_MODULUS)) for _ in range(size)] 
            for _ in range(size)]

def generate_lwe_sbox(master_key: bytes, sbox_index: int, counter: int) -> List[int]:
    h = hashlib.sha256()
    h.update(master_key)
    h.update(sbox_index.to_bytes(1, 'big'))
    h.update(counter.to_bytes(8, 'big'))
    seed = h.digest()

    rng = np.random.RandomState(int.from_bytes(seed[:4], 'big'))
    A = [[int(rng.randint(0, LWE_MODULUS)) for _ in range(SBOX_SIZE)] 
         for _ in range(SBOX_SIZE)]
    
    sbox = []
    for x in range(SBOX_SIZE):
        error_seed = hashlib.sha256(seed + x.to_bytes(2, 'big')).digest()
        error = int.from_bytes(error_seed[:2], 'big') % LWE_MODULUS
        
        ax_sum = sum(A[x]) % LWE_MODULUS
        value = (ax_sum * x + error) % LWE_MODULUS

        sbox.append(value % 256)

    return ensure_bijection(sbox)
def ensure_bijection(sbox: List[int]) -> List[int]:
    used = set()
    result = []
    available = list(range(256))
    
    for val in sbox:
        if val not in used:
            result.append(val)
            used.add(val)
            if val in available:
                available.remove(val)
        else:
            replacement = available.pop(0)
            result.append(replacement)
            used.add(replacement)
    
    return result

def generate_ntru_permutation(round_key: bytes, round_num: int) -> List[int]:
    h = hashlib.sha256()
    h.update(round_key)
    h.update(round_num.to_bytes(1, 'big'))
    seed = int.from_bytes(h.digest(), 'big')
    
    rng = np.random.RandomState(seed % (2**32))
    permutation = list(range(NTRU_N))
    rng.shuffle(permutation)
    
    return permutation

def generate_lattice_constant(round_num: int, word_idx: int) -> int:
    h = hashlib.sha256()
    h.update(b"NEXUS-LATTICE")
    h.update(round_num.to_bytes(1, 'big'))
    h.update(word_idx.to_bytes(1, 'big'))
    return int.from_bytes(h.digest()[:16], 'big')

def hkdf_sha256(input_key: bytes, length: int, info: bytes = b"") -> bytes:
    h = hashlib.sha256()
    h.update(input_key)
    prk = h.digest()

    okm = b""
    t = b""
    for i in range((length + 31) // 32):
        h = hashlib.sha256()
        h.update(t)
        h.update(prk)  
        h.update(info)
        h.update(bytes([i + 1]))
        t = h.digest()
        okm += t
    
    return okm[:length]