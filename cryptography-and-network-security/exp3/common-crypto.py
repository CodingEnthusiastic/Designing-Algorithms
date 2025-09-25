# common_crypto.py
import base64, random, string, time
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.Random import get_random_bytes

# ---------- base64 helpers ----------
def b64(b: bytes) -> str:
    return base64.b64encode(b).decode()

def ub64(s: str) -> bytes:
    return base64.b64decode(s.encode())

# ---------- RSA helpers ----------
def gen_rsa_keypair(bits=2048):
    key = RSA.generate(bits)
    return key.export_key(), key.publickey().export_key()

def rsa_sign(private_pem: bytes, message: bytes) -> bytes:
    key = RSA.import_key(private_pem)
    h = SHA256.new(message)
    signer = pkcs1_15.new(key)
    return signer.sign(h)

def rsa_verify(public_pem: bytes, message: bytes, signature: bytes) -> bool:
    key = RSA.import_key(public_pem)
    h = SHA256.new(message)
    verifier = pkcs1_15.new(key)
    try:
        verifier.verify(h, signature)
        return True
    except (ValueError, TypeError):
        return False

def rsa_encrypt(public_pem: bytes, plaintext: bytes) -> bytes:
    key = RSA.import_key(public_pem)
    cipher = PKCS1_OAEP.new(key)
    return cipher.encrypt(plaintext)

def rsa_decrypt(private_pem: bytes, ciphertext: bytes) -> bytes:
    key = RSA.import_key(private_pem)
    cipher = PKCS1_OAEP.new(key)
    return cipher.decrypt(ciphertext)

# ---------- AES-GCM ----------
def aes_gcm_encrypt(key: bytes, plaintext: bytes, aad: bytes = b""):
    cipher = AES.new(key, AES.MODE_GCM)
    cipher.update(aad)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    return cipher.nonce, ciphertext, tag

def aes_gcm_decrypt(key: bytes, nonce: bytes, ciphertext: bytes, tag: bytes, aad: bytes = b""):
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    cipher.update(aad)
    return cipher.decrypt_and_verify(ciphertext, tag)

# ---------- AES-CBC with PKCS7 ----------
def _pkcs7_pad(data: bytes, block_size=16) -> bytes:
    pad_len = block_size - (len(data) % block_size)
    return data + bytes([pad_len]) * pad_len

def _pkcs7_unpad(padded: bytes) -> bytes:
    if not padded:
        raise ValueError("Invalid padding (empty)")
    pad_len = padded[-1]
    if pad_len < 1 or pad_len > 16:
        raise ValueError("Invalid padding length")
    if padded[-pad_len:] != bytes([pad_len]) * pad_len:
        raise ValueError("Invalid padding bytes")
    return padded[:-pad_len]

def aes_cbc_encrypt(key: bytes, iv: bytes, plaintext: bytes):
    cipher = AES.new(key, AES.MODE_CBC, iv)
    pt = _pkcs7_pad(plaintext, AES.block_size)
    ct = cipher.encrypt(pt)
    return ct

def aes_cbc_decrypt(key: bytes, iv: bytes, ciphertext: bytes):
    cipher = AES.new(key, AES.MODE_CBC, iv)
    pt_padded = cipher.decrypt(ciphertext)
    return _pkcs7_unpad(pt_padded)

def gen_aes_key_iv(key_bytes=16):
    return get_random_bytes(key_bytes), get_random_bytes(16)

# ---------- Hybrid (RSA + AES-GCM) ----------
def hybrid_encrypt(receiver_public_pem: bytes, payload: bytes):
    sym_key = get_random_bytes(32)  # 256-bit symmetric key
    nonce, ciphertext, tag = aes_gcm_encrypt(sym_key, payload)
    enc_sym_key = rsa_encrypt(receiver_public_pem, sym_key)
    return enc_sym_key, nonce, ciphertext, tag

def hybrid_decrypt(receiver_private_pem: bytes, enc_sym_key: bytes, nonce: bytes, ciphertext: bytes, tag: bytes):
    sym_key = rsa_decrypt(receiver_private_pem, enc_sym_key)
    return aes_gcm_decrypt(sym_key, nonce, ciphertext, tag)

# ---------- toy utilities ----------
def gen_toy_symmetric_key(min_len=200, max_len=300):
    length = random.randint(min_len, max_len)
    letters = string.ascii_uppercase + string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))

def gen_toy_asymmetric_key(min_len=20, max_len=30):
    length = random.randint(min_len, max_len)
    letters = string.ascii_uppercase + string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))

# mapping helpers (for lab display)
def create_letter_number_map():
    m = {}
    num = 1
    for c in string.ascii_uppercase:
        m[c] = f"{num:02d}"; num += 1
    for c in string.ascii_lowercase:
        m[c] = f"{num:02d}"; num += 1
    m[' '] = "00"
    for d in string.digits:
        m[d] = f"{num:02d}"; num += 1
    return m

_letter_number_map = create_letter_number_map()
_number_letter_map = {v: k for k, v in _letter_number_map.items()}

def map_text_to_numbers(text: str) -> str:
    out = []
    for ch in text:
        if ch in _letter_number_map:
            out.append(_letter_number_map[ch])
        else:
            out.append("??")
    return ' '.join(out)

def map_numbers_to_text(numstr: str) -> str:
    parts = numstr.split()
    out = []
    for p in parts:
        out.append(_number_letter_map.get(p, '?'))
    return ''.join(out)

# ---------- Performance comparison ----------
def performance_compare(payload: bytes, public_pem: bytes=None, private_pem: bytes=None, repeats=3):
    res = {}
    # AES-GCM 256
    kg = get_random_bytes(32)
    g_enc_total = g_dec_total = 0.0
    for _ in range(repeats):
        t0 = time.perf_counter()
        nonce, ct, tag = aes_gcm_encrypt(kg, payload)
        t1 = time.perf_counter()
        _ = aes_gcm_decrypt(kg, nonce, ct, tag)
        t2 = time.perf_counter()
        g_enc_total += (t1 - t0)
        g_dec_total += (t2 - t1)
    res['aes_gcm_enc'] = g_enc_total / repeats
    res['aes_gcm_dec'] = g_dec_total / repeats

    # AES-CBC 128
    kcbc = get_random_bytes(16)
    iv = get_random_bytes(16)
    c_enc_total = c_dec_total = 0.0
    for _ in range(repeats):
        t0 = time.perf_counter()
        ct = aes_cbc_encrypt(kcbc, iv, payload)
        t1 = time.perf_counter()
        _ = aes_cbc_decrypt(kcbc, iv, ct)
        t2 = time.perf_counter()
        c_enc_total += (t1 - t0)
        c_dec_total += (t2 - t1)
    res['aes_cbc_enc'] = c_enc_total / repeats
    res['aes_cbc_dec'] = c_dec_total / repeats

    # RSA and Hybrid if keys provided
    if public_pem and private_pem:
        rsa_enc_total = rsa_dec_total = 0.0
        test_chunk = get_random_bytes(32)
        for _ in range(repeats):
            t0 = time.perf_counter()
            enc = rsa_encrypt(public_pem, test_chunk)
            t1 = time.perf_counter()
            dec = rsa_decrypt(private_pem, enc)
            t2 = time.perf_counter()
            rsa_enc_total += (t1 - t0)
            rsa_dec_total += (t2 - t1)
        res['rsa_enc'] = rsa_enc_total / repeats
        res['rsa_dec'] = rsa_dec_total / repeats

        hy_enc_total = hy_dec_total = 0.0
        for _ in range(repeats):
            t0 = time.perf_counter()
            enc_sym = rsa_encrypt(public_pem, get_random_bytes(32))
            nonce, ct, tag = aes_gcm_encrypt(get_random_bytes(32), payload)
            t1 = time.perf_counter()
            # simulate decrypt steps
            _ = rsa_decrypt(private_pem, enc_sym)
            try:
                _ = aes_gcm_decrypt(get_random_bytes(32), nonce, ct, tag) if len(payload) > 0 else b''
            except:
                pass
            t2 = time.perf_counter()
            hy_enc_total += (t1 - t0)
            hy_dec_total += (t2 - t1)
        res['hybrid_enc'] = hy_enc_total / repeats
        res['hybrid_dec'] = hy_dec_total / repeats
    else:
        res['rsa_enc'] = res['rsa_dec'] = None
        res['hybrid_enc'] = res['hybrid_dec'] = None

    return res
