# tpe_server.py
import socket, threading, json, os, traceback, struct
from common_crypto import *
from base64 import b64encode, b64decode

DB_FILE = "tpe_keys_db.json"
TPE_HOST = "0.0.0.0"
TPE_PORT = 5000

CRYPTO_HOST = "0.0.0.0"
CRYPTO_PORT = 6000

# ---------- length-prefixed helpers ----------
def recv_all(sock, n):
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            return None
        data += chunk
    return data

def recv_msg(sock):
    hdr = recv_all(sock, 4)
    if not hdr:
        return None
    (length,) = struct.unpack("!I", hdr)
    data = recv_all(sock, length)
    if data is None:
        return None
    return data.decode()

def send_msg(sock, obj):
    data = json.dumps(obj).encode()
    hdr = struct.pack("!I", len(data))
    sock.sendall(hdr + data)

# ---------- DB helpers ----------
def load_db():
    if os.path.exists(DB_FILE):
        try:
            return json.load(open(DB_FILE, "r"))
        except:
            return {}
    return {}

def save_db(db):
    json.dump(db, open(DB_FILE, "w"), indent=2)

# ---------- TPE handler ----------
def handle_tpe_client(conn, addr):
    try:
        body = recv_msg(conn)
        if not body:
            return
        req = json.loads(body)
        cmd = req.get("cmd")
        if cmd == "register":
            identity = req.get("id")
            pub = req.get("pub")
            if not identity or not pub:
                resp = {"status":"error","error":"missing id or pub"}
            else:
                db = load_db()
                db[identity] = pub
                save_db(db)
                resp = {"status":"ok","id":identity}
                print(f"[TPE] Registered: {identity}")
        elif cmd == "get_key":
            identity = req.get("id")
            db = load_db()
            if identity in db:
                resp = {"status":"ok","id":identity,"pub":db[identity]}
            else:
                resp = {"status":"error","error":"not found"}
        else:
            resp = {"status":"error","error":"unknown command"}
    except Exception as e:
        resp = {"status":"error","error":str(e)}
    try:
        send_msg(conn, resp)
    except:
        pass
    finally:
        conn.close()

def start_tpe_server(host=TPE_HOST, port=TPE_PORT):
    print(f"[TPE] Starting socket TPE on {host}:{port}")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.listen(5)
    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle_tpe_client, args=(conn, addr), daemon=True).start()

# ---------- Crypto handler (length-prefixed) ----------
def handle_crypto_client(conn, addr):
    try:
        body = recv_msg(conn)
        if not body:
            return
        req = json.loads(body)
        cmd = req.get("cmd")
        resp = {"status":"error","error":"unknown command"}
        # AES
        if cmd == "aes_enc":
            mode = req.get("mode","gcm").lower()
            key_b64 = req.get("key","")
            iv_b64 = req.get("iv","")
            plaintext = req.get("plaintext","")
            plaintext_bytes = plaintext.encode() if isinstance(plaintext,str) else b""
            if req.get("plain_b64", False):
                plaintext_bytes = b64decode(plaintext)
            if not key_b64:
                if mode == "gcm":
                    key = get_random_bytes(32)
                else:
                    key = get_random_bytes(16)
                key_b64 = b64encode(key).decode()
            else:
                key = b64decode(key_b64)
            if mode == "gcm":
                nonce, ct, tag = aes_gcm_encrypt(key, plaintext_bytes)
                resp = {"status":"ok", "nonce": b64encode(nonce).decode(), "ciphertext": b64encode(ct).decode(), "tag": b64encode(tag).decode(), "key": key_b64}
            else:
                if not iv_b64:
                    iv = get_random_bytes(16)
                    iv_b64 = b64encode(iv).decode()
                else:
                    iv = b64decode(iv_b64)
                ct = aes_cbc_encrypt(key, iv, plaintext_bytes)
                resp = {"status":"ok", "iv": iv_b64, "ciphertext": b64encode(ct).decode(), "key": key_b64}

        elif cmd == "aes_dec":
            mode = req.get("mode","gcm").lower()
            key = b64decode(req.get("key",""))
            if mode == "gcm":
                nonce = b64decode(req.get("nonce",""))
                ct = b64decode(req.get("ciphertext",""))
                tag = b64decode(req.get("tag",""))
                try:
                    pt = aes_gcm_decrypt(key, nonce, ct, tag)
                    resp = {"status":"ok", "plaintext": b64encode(pt).decode(), "plaintext_utf": pt.decode(errors="ignore")}
                except Exception as e:
                    resp = {"status":"error","error":f"decrypt failed: {e}"}
            else:
                iv = b64decode(req.get("iv",""))
                ct = b64decode(req.get("ciphertext",""))
                try:
                    pt = aes_cbc_decrypt(key, iv, ct)
                    resp = {"status":"ok", "plaintext": b64encode(pt).decode(), "plaintext_utf": pt.decode(errors="ignore")}
                except Exception as e:
                    resp = {"status":"error","error":f"decrypt failed: {e}"}

        # RSA
        elif cmd == "rsa_enc":
            pub_b64 = req.get("pub","")
            plaintext = req.get("plaintext","")
            plaintext_bytes = b64decode(plaintext) if req.get("plain_b64", False) else plaintext.encode()
            pub_pem = b64decode(pub_b64)
            try:
                ct = rsa_encrypt(pub_pem, plaintext_bytes)
                resp = {"status":"ok","ciphertext": b64encode(ct).decode()}
            except Exception as e:
                resp = {"status":"error","error":str(e)}

        elif cmd == "rsa_dec":
            priv_b64 = req.get("priv","")
            ct_b64 = req.get("ciphertext","")
            priv_pem = b64decode(priv_b64)
            try:
                pt = rsa_decrypt(priv_pem, b64decode(ct_b64))
                resp = {"status":"ok","plaintext": b64encode(pt).decode(), "plaintext_utf": pt.decode(errors="ignore")}
            except Exception as e:
                resp = {"status":"error","error":str(e)}

        # Hybrid
        elif cmd == "hybrid_enc":
            pub_b64 = req.get("pub","")
            plaintext = req.get("plaintext","")
            plaintext_bytes = b64decode(plaintext) if req.get("plain_b64", False) else plaintext.encode()
            pub_pem = b64decode(pub_b64)
            try:
                enc_sym_key, nonce, ct, tag = hybrid_encrypt(pub_pem, plaintext_bytes)
                resp = {"status":"ok", "enc_sym_key": b64encode(enc_sym_key).decode(), "nonce": b64encode(nonce).decode(), "ciphertext": b64encode(ct).decode(), "tag": b64encode(tag).decode()}
            except Exception as e:
                resp = {"status":"error","error":str(e)}

        elif cmd == "hybrid_dec":
            priv_b64 = req.get("priv","")
            enc_sym_key_b64 = req.get("enc_sym_key","")
            nonce_b64 = req.get("nonce","")
            ct_b64 = req.get("ciphertext","")
            tag_b64 = req.get("tag","")
            try:
                pt = hybrid_decrypt(b64decode(priv_b64), b64decode(enc_sym_key_b64), b64decode(nonce_b64), b64decode(ct_b64), b64decode(tag_b64))
                resp = {"status":"ok","plaintext": b64encode(pt).decode(), "plaintext_utf": pt.decode(errors="ignore")}
            except Exception as e:
                resp = {"status":"error","error":str(e)}

        # perf
        elif cmd == "perf_compare":
            payload = req.get("payload","")
            payload_bytes = payload.encode() if not req.get("payload_b64", False) else b64decode(payload)
            pub_b64 = req.get("pub","") or None
            priv_b64 = req.get("priv","") or None
            pub_pem = b64decode(pub_b64) if pub_b64 else None
            priv_pem = b64decode(priv_b64) if priv_b64 else None
            try:
                timings = performance_compare(payload_bytes, public_pem=pub_pem, private_pem=priv_pem, repeats=3)
                resp = {"status":"ok", "timings": timings}
            except Exception as e:
                resp = {"status":"error","error":str(e)}

        else:
            resp = {"status":"error","error":"unknown command"}

    except Exception as e:
        traceback.print_exc()
        resp = {"status":"error","error": str(e)}
    try:
        send_msg(conn, resp)
    except:
        pass
    finally:
        conn.close()

def start_crypto_server(host=CRYPTO_HOST, port=CRYPTO_PORT):
    print(f"[CRYPTO] Starting crypto service on {host}:{port}")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.listen(5)
    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle_crypto_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    threading.Thread(target=start_tpe_server, daemon=True).start()
    threading.Thread(target=start_crypto_server, daemon=True).start()
    print("[MAIN] TPE and Crypto services started. Ctrl-C to exit.")
    while True:
        try:
            threading.Event().wait(1)
        except KeyboardInterrupt:
            print("Shutting down.")
            break
