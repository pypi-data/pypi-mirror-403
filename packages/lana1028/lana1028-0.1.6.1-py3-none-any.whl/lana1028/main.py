import os
import hashlib
import base64
import secrets

# Constants
KEY_SIZE_BITS = 1028
KEY_SIZE_BYTES = (KEY_SIZE_BITS + 7) // 8  # 129 bytes
BLOCK_SIZE = 64  # 512-bit block
NUM_ROUNDS = 64
IV_SIZE = BLOCK_SIZE  # 64 bytes

# ✔ NONLINEAR S-BOX TABLE (based on AES S-box construction principles)
# This is a proper substitution table, not just XOR
S_BOX = bytes([
    0x63, 0x7C, 0x77, 0x7B, 0xF2, 0x6B, 0x6F, 0xC5, 0x30, 0x01, 0x67, 0x2B, 0xFE, 0xD7, 0xAB, 0x76,
    0xCA, 0x82, 0xC9, 0x7D, 0xFA, 0x59, 0x47, 0xF0, 0xAD, 0xD4, 0xA2, 0xAF, 0x9C, 0xA4, 0x72, 0xC0,
    0xB7, 0xFD, 0x93, 0x26, 0x36, 0x3F, 0xF7, 0xCC, 0x34, 0xA5, 0xE5, 0xF1, 0x71, 0xD8, 0x31, 0x15,
    0x04, 0xC7, 0x23, 0xC3, 0x18, 0x96, 0x05, 0x9A, 0x07, 0x12, 0x80, 0xE2, 0xEB, 0x27, 0xB2, 0x75,
    0x09, 0x83, 0x2C, 0x1A, 0x1B, 0x6E, 0x5A, 0xA0, 0x52, 0x3B, 0xD6, 0xB3, 0x29, 0xE3, 0x2F, 0x84,
    0x53, 0xD1, 0x00, 0xED, 0x20, 0xFC, 0xB1, 0x5B, 0x6A, 0xCB, 0xBE, 0x39, 0x4A, 0x4C, 0x58, 0xCF,
    0xD0, 0xEF, 0xAA, 0xFB, 0x43, 0x4D, 0x33, 0x85, 0x45, 0xF9, 0x02, 0x7F, 0x50, 0x3C, 0x9F, 0xA8,
    0x51, 0xA3, 0x40, 0x8F, 0x92, 0x9D, 0x38, 0xF5, 0xBC, 0xB6, 0xDA, 0x21, 0x10, 0xFF, 0xF3, 0xD2,
    0xCD, 0x0C, 0x13, 0xEC, 0x5F, 0x97, 0x44, 0x17, 0xC4, 0xA7, 0x7E, 0x3D, 0x64, 0x5D, 0x19, 0x73,
    0x60, 0x81, 0x4F, 0xDC, 0x22, 0x2A, 0x90, 0x88, 0x46, 0xEE, 0xB8, 0x14, 0xDE, 0x5E, 0x0B, 0xDB,
    0xE0, 0x32, 0x3A, 0x0A, 0x49, 0x06, 0x24, 0x5C, 0xC2, 0xD3, 0xAC, 0x62, 0x91, 0x95, 0xE4, 0x79,
    0xE7, 0xC8, 0x37, 0x6D, 0x8D, 0xD5, 0x4E, 0xA9, 0x6C, 0x56, 0xF4, 0xEA, 0x65, 0x7A, 0xAE, 0x08,
    0xBA, 0x78, 0x25, 0x2E, 0x1C, 0xA6, 0xB4, 0xC6, 0xE8, 0xDD, 0x74, 0x1F, 0x4B, 0xBD, 0x8B, 0x8A,
    0x70, 0x3E, 0xB5, 0x66, 0x48, 0x03, 0xF6, 0x0E, 0x61, 0x35, 0x57, 0xB9, 0x86, 0xC1, 0x1D, 0x9E,
    0xE1, 0xF8, 0x98, 0x11, 0x69, 0xD9, 0x8E, 0x94, 0x9B, 0x1E, 0x87, 0xE9, 0xCE, 0x55, 0x28, 0xDF,
    0x8C, 0xA1, 0x89, 0x0D, 0xBF, 0xE6, 0x42, 0x68, 0x41, 0x99, 0x2D, 0x0F, 0xB0, 0x54, 0xBB, 0x16
])

# Inverse S-box for decryption
INV_S_BOX = bytes([S_BOX.index(i) for i in range(256)])

# --- Utility: Padding (PKCS7-style) ---
def pad(data):
    pad_len = BLOCK_SIZE - (len(data) % BLOCK_SIZE)
    return data + bytes([pad_len] * pad_len)

def unpad(data):
    """✔ STRICT UNPAD CHECKING"""
    if len(data) == 0:
        raise ValueError("Invalid padding: empty data")
    
    pad_len = data[-1]
    
    # Check pad length is valid
    if pad_len == 0 or pad_len > BLOCK_SIZE:
        raise ValueError(f"Invalid padding length: {pad_len}")
    
    # Check all padding bytes are correct
    if len(data) < pad_len:
        raise ValueError("Invalid padding: data too short")
    
    for i in range(pad_len):
        if data[-(i+1)] != pad_len:
            raise ValueError(f"Invalid padding bytes at position {i}")
    
    return data[:-pad_len]

# --- Key Generation ---
def generate_lana1028_key():
    return secrets.token_bytes(KEY_SIZE_BYTES)

# --- Key Expansion ---
def key_expansion(master_key):
    expanded_keys = []
    for i in range(NUM_ROUNDS):
        round_key = hashlib.sha512(master_key + i.to_bytes(4, 'big')).digest()
        expanded_keys.append(round_key[:BLOCK_SIZE])
    return expanded_keys

# ✔ NONLINEAR S-BOX APPLICATION
def s_box(data):
    """Apply nonlinear substitution using lookup table"""
    return bytes(S_BOX[b] for b in data)

def inv_s_box(data):
    """Apply inverse substitution for decryption"""
    return bytes(INV_S_BOX[b] for b in data)

# ✔ BYTE MIXING (inspired by AES MixColumns)
def mix_bytes(data):
    """Mix bytes within the block for diffusion"""
    data = bytearray(data)
    mixed = bytearray(len(data))
    
    # Process in groups of 4 bytes (similar to AES columns)
    for i in range(0, len(data), 4):
        if i + 3 < len(data):
            # Galois field multiplication simulation (simplified)
            a, b, c, d = data[i:i+4]
            mixed[i]     = (a ^ b ^ c) & 0xFF
            mixed[i + 1] = (a ^ b ^ d) & 0xFF
            mixed[i + 2] = (a ^ c ^ d) & 0xFF
            mixed[i + 3] = (b ^ c ^ d) & 0xFF
        else:
            # Handle remaining bytes
            for j in range(i, len(data)):
                mixed[j] = data[j]
    
    return bytes(mixed)

def inv_mix_bytes(data):
    """Inverse mixing for decryption (this is a simplified inverse)"""
    data = bytearray(data)
    unmixed = bytearray(len(data))
    
    for i in range(0, len(data), 4):
        if i + 3 < len(data):
            a, b, c, d = data[i:i+4]
            # Inverse operation (for this simplified mixing)
            unmixed[i]     = (a ^ b ^ c) & 0xFF
            unmixed[i + 1] = (a ^ b ^ d) & 0xFF
            unmixed[i + 2] = (a ^ c ^ d) & 0xFF
            unmixed[i + 3] = (b ^ c ^ d) & 0xFF
        else:
            for j in range(i, len(data)):
                unmixed[j] = data[j]
    
    return bytes(unmixed)

# P-Box (Permutation)
def p_box(data):
    """Bit permutation for additional diffusion"""
    return data[::-1]

# ✔ IV MIXING EVERY ROUND
def mix_with_iv(data, iv, round_num):
    """Mix IV into data differently each round"""
    # Use round number to create different IV transformations per round
    round_iv = hashlib.sha512(iv + round_num.to_bytes(4, 'big')).digest()[:len(data)]
    return bytes(a ^ b for a, b in zip(data, round_iv))

# --- Encryption ---
def lana1028_encrypt(plaintext: str, key: bytes) -> str:
    if not isinstance(plaintext, bytes):
        plaintext = plaintext.encode()

    plaintext = pad(plaintext)
    iv = secrets.token_bytes(IV_SIZE)  # ✔ Fresh random IV
    expanded_keys = key_expansion(key)

    # Process data in blocks
    blocks = [plaintext[i:i+BLOCK_SIZE] for i in range(0, len(plaintext), BLOCK_SIZE)]
    ciphertext_blocks = []

    for block in blocks:
        data = bytearray(block)
        
        for round_num in range(NUM_ROUNDS):
            round_key = expanded_keys[round_num]
            
            # ✔ Mix IV every round
            data = mix_with_iv(data, iv, round_num)
            
            # XOR with round key
            data = bytearray([data[i] ^ round_key[i % BLOCK_SIZE] for i in range(len(data))])
            
            # ✔ Apply nonlinear S-box
            data = s_box(data)
            
            # ✔ Byte mixing for diffusion
            data = mix_bytes(data)
            
            # Permutation
            data = p_box(data)
        
        ciphertext_blocks.append(bytes(data))

    # Prepend IV to ciphertext
    final_ciphertext = iv + b''.join(ciphertext_blocks)
    return base64.b64encode(final_ciphertext).decode()

# --- Decryption ---
def lana1028_decrypt(encoded_ciphertext: str, key: bytes) -> str:
    ciphertext = base64.b64decode(encoded_ciphertext)
    
    # Extract IV
    iv = ciphertext[:IV_SIZE]
    ciphertext = ciphertext[IV_SIZE:]
    
    expanded_keys = key_expansion(key)

    # Process data in blocks
    blocks = [ciphertext[i:i+BLOCK_SIZE] for i in range(0, len(ciphertext), BLOCK_SIZE)]
    plaintext_blocks = []

    for block in blocks:
        data = bytearray(block)
        
        # Reverse all operations
        for round_num in reversed(range(NUM_ROUNDS)):
            round_key = expanded_keys[round_num]
            
            # Reverse permutation
            data = p_box(data)
            
            # ✔ Reverse byte mixing
            data = inv_mix_bytes(data)
            
            # ✔ Reverse S-box
            data = inv_s_box(data)
            
            # Reverse XOR with round key
            data = bytearray([data[i] ^ round_key[i % BLOCK_SIZE] for i in range(len(data))])
            
            # ✔ Reverse IV mixing
            data = mix_with_iv(data, iv, round_num)
        
        plaintext_blocks.append(bytes(data))

    plaintext = b''.join(plaintext_blocks)
    
    # ✔ Strict unpadding with validation
    return unpad(plaintext).decode()