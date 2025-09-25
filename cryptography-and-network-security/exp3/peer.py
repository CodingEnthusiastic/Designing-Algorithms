# peer.py
import os, json, socket, threading, time, struct
from common_crypto import *
from pathlib import Path
from base64 import b64encode, b64decode

TPE_HOST = input("Enter TPE server IP (default 127.0.0.1): ").strip() or "127.0.0.1"
TPE_PORT = int(input("Enter TPE server port (default 5000): ").strip() or "5000")
REPLAY_WINDOW = 30
REKEY_AFTER = 5

# ---------- length-prefixed helpers (match server) ----------
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

# ---------- functions that use TPE / Crypto servers ----------
def tpe_request(req_json, timeout=5):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((TPE_HOST, TPE_PORT))
        send_msg(s, req_json)
        resp_text = recv_msg(s)
        if not resp_text:
            return None
        return json.loads(resp_text)
    except Exception as e:
        print("[TPE CLIENT] Error contacting TPE:", e)
        return None
    finally:
        try:
            s.close()
        except:
            pass

def crypto_request(host, port, req_json, timeout=20):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        send_msg(s, req_json)
        resp_text = recv_msg(s)
        if not resp_text:
            return None
        return json.loads(resp_text)
    except Exception as e:
        print("[CRYPTO CLIENT] Error contacting crypto service:", e)
        return None
    finally:
        try:
            s.close()
        except:
            pass

# ---------- key helpers ----------
def ensure_keys(identity):
    d = Path(f"keys_{identity}")
    d.mkdir(exist_ok=True)
    priv_path = d / "priv.pem"
    pub_path = d / "pub.pem"
    toy_asym_path = d / "toy_asym.txt"
    if not (priv_path.exists() and pub_path.exists()):
        print(f"[{identity}] Generating RSA key pair (2048 bits)...")
        priv, pub = gen_rsa_keypair(2048)
        priv_path.write_bytes(priv)
        pub_path.write_bytes(pub)
        print(f"[{identity}] Keys saved under {d}/")
    else:
        print(f"[{identity}] Keys found under {d}/")
    if not toy_asym_path.exists():
        toy = gen_toy_asymmetric_key(20,30)
        toy_asym_path.write_text(toy)
    else:
        toy = toy_asym_path.read_text()
    print(f"[{identity}] Toy asymmetric key (20-30 letters) for lab display: {toy}")
    return priv_path.read_bytes(), pub_path.read_bytes(), str(d)

def register_with_tpe(identity, pub_pem):
    print(f"[{identity}] Registering public key with TPE...")
    req = {"cmd":"register","id":identity,"pub":b64encode(pub_pem).decode()}
    resp = tpe_request(req)
    if resp and resp.get("status") == "ok":
        print(f"[{identity}] Registration success.")
    else:
        print(f"[{identity}] Registration failed: {resp}")

def fetch_pub_from_tpe(identity, keydir, who):
    print(f"[{who}] Fetching {identity}'s public key from TPE...")
    req = {"cmd":"get_key","id":identity}
    resp = tpe_request(req)
    if resp and resp.get("status") == "ok":
        pub_b64 = resp.get("pub")
        kr_path = os.path.join(keydir, "keyring.json")
        kr = {}
        if os.path.exists(kr_path):
            kr = json.load(open(kr_path, "r"))
        kr[identity] = pub_b64
        json.dump(kr, open(kr_path, "w"), indent=2)
        print(f"[{who}] Stored {identity} pub in local keyring.")
        return b64decode(pub_b64)
    else:
        print(f"[{who}] TPE get_key failed: {resp}")
        return None

def get_pubkey(identity, keydir, who):
    kr_path = os.path.join(keydir, "keyring.json")
    if os.path.exists(kr_path):
        kr = json.load(open(kr_path, "r"))
        if identity in kr:
            print(f"[{who}] Found {identity}'s key in local keyring.")
            return b64decode(kr[identity])
    return fetch_pub_from_tpe(identity, keydir, who)

sessions = {}

# ---------- server that accepts handshake / message / close_notify ----------
def start_peer_server(identity, priv_pem, pub_pem, keydir, listen_host, listen_port):
    def handle_connection(conn, addr):
        try:
            body = recv_msg(conn)
            if not body:
                return
            msg = json.loads(body)
            mtype = msg.get("type")
            if mtype == "handshake":
                print(f"\n[{identity} SERVER] Received handshake from {msg.get('sender')} @ {addr}")
                handle_incoming_handshake(identity, priv_pem, pub_pem, keydir, msg)
            elif mtype == "message":
                print(f"\n[{identity} SERVER] Received message from {msg.get('sender')} @ {addr}")
                handle_incoming_message(identity, priv_pem, pub_pem, keydir, msg)
            elif mtype == "close_notify":
                print(f"\n[{identity} SERVER] Received close_notify from {msg.get('sender')} @ {addr}")
                handle_close_notify(identity, priv_pem, pub_pem, keydir, msg)
            elif mtype == "chat":
                # optional -- chat type (simple AES-GCM encrypted body)
                sender = msg.get("sender")
                if sender not in sessions:
                    print(f"[{identity}] No session with {sender}. Cannot decrypt chat.")
                    return
                sess = sessions[sender]
                try:
                    pt = aes_gcm_decrypt(sess["sym_key"], b64decode(msg["nonce"]), b64decode(msg["ciphertext"]), b64decode(msg["tag"]))
                    print(f"\n[{identity}] [CHAT from {sender}]: {pt.decode()}")
                except Exception as e:
                    print(f"[{identity}] Chat decrypt error: {e}")
            else:
                print(f"[{identity} SERVER] Unknown message type: {mtype}")
        except Exception as e:
            print(f"[{identity} SERVER] Error handling connection: {e}")
        finally:
            conn.close()

    def server_loop():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((listen_host, listen_port))
        s.listen(5)
        print(f"[{identity} SERVER] Listening on {listen_host}:{listen_port} for incoming peer connections...")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_connection, args=(conn, addr), daemon=True).start()

    t = threading.Thread(target=server_loop, daemon=True)
    t.start()
    return t

def handle_incoming_handshake(identity, priv_pem, pub_pem, keydir, msg):
    sender = msg.get("sender")
    try:
        enc_sym_key = b64decode(msg["enc_sym_key"])
        nonce = b64decode(msg["nonce"])
        ciphertext = b64decode(msg["ciphertext"])
        tag = b64decode(msg["tag"])
        payload = hybrid_decrypt(priv_pem, enc_sym_key, nonce, ciphertext, tag)
        dh_secret, signature = payload.split(b"::SIG::")
    except Exception as e:
        print(f"[{identity}] Handshake error: {e}")
        return
    sender_pub = get_pubkey(sender, keydir, identity)
    if not sender_pub or not rsa_verify(sender_pub, dh_secret, signature):
        print(f"[{identity}] Handshake signature verification failed from {sender}")
        return
    sym_key = SHA256.new(dh_secret).digest()
    toy_sym = gen_toy_symmetric_key(200, 240)
    sessions[sender] = {"sym_key": sym_key, "dh_secret": dh_secret, "msg_count": 0, "seen_ts": set(), "toy_sym": toy_sym}
    print(f"[{identity}] Session established with {sender}. Symmetric key derived.")
    print(f"[{identity}] Toy symmetric key for lab (200-240 letters): {toy_sym[:80]}... (len={len(toy_sym)})")
    sample_plain = "Demo"
    print(f"[{identity}] Sample mapping A->01 etc: '{sample_plain}' -> {map_text_to_numbers(sample_plain)}")

def handle_incoming_message(identity, priv_pem, pub_pem, keydir, msg):
    sender = msg.get("sender")
    if sender not in sessions:
        print(f"[{identity}] No session with {sender}. Cannot decrypt message.")
        return
    ts = msg.get("ts")
    now = int(time.time())
    if abs(now - ts) > REPLAY_WINDOW or ts in sessions[sender]["seen_ts"]:
        print(f"[{identity}] Replay/expired message rejected from {sender}")
        return
    sessions[sender]["seen_ts"].add(ts)
    sess = sessions[sender]
    try:
        plaintext = aes_gcm_decrypt(sess["sym_key"], b64decode(msg["nonce"]), b64decode(msg["ciphertext"]), b64decode(msg["tag"]))
    except Exception as e:
        print(f"[{identity}] AES decryption failed: {e}")
        return
    sender_pub = get_pubkey(sender, keydir, identity)
    ok = rsa_verify(sender_pub, plaintext, b64decode(msg["signature"]))
    if ok:
        print(f"[{identity}] Decrypted plaintext: {plaintext.decode()}")
        print(f"[{identity}] Signature verification for message from {sender}: True")
        mapped = map_text_to_numbers(plaintext.decode()[:60])
        print(f"[{identity}] Plaintext->Numbers (sample first 60 chars): {mapped[:200]}")
        remap = map_numbers_to_text(' '.join(mapped.split()[:10]))
        print(f"[{identity}] Numbers->Text (sample): {remap}")
    else:
        print(f"[{identity}] Signature verification for message from {sender}: False")
    sess["msg_count"] += 1
    if sess["msg_count"] >= REKEY_AFTER:
        print(f"[{identity}] Rekey triggered with {sender} after {sess['msg_count']} messages. Session dropped.")
        del sessions[sender]

def handle_close_notify(identity, priv_pem, pub_pem, keydir, msg):
    sender = msg.get("sender")
    if sender not in sessions:
        print(f"[{identity}] No session with {sender} to close.")
        return
    sender_pub = get_pubkey(sender, keydir, identity)
    if rsa_verify(sender_pub, b"CLOSE_SESSION", b64decode(msg["signature"])):
        del sessions[sender]
        print(f"[{identity}] Session with {sender} terminated by close_notify.")
    else:
        print(f"[{identity}] Bad close_notify signature from {sender}")

def send_handshake_to_peer(identity, priv_pem, pub_pem, keydir, target_ip, target_port, receiver_id):
    print(f"[{identity}] Preparing SSL-1 handshake for {receiver_id} -> {target_ip}:{target_port}")
    recv_pub = get_pubkey(receiver_id, keydir, identity)
    if not recv_pub:
        print(f"[{identity}] Receiver public key not available.")
        return
    dh_secret = get_random_bytes(32)
    signature = rsa_sign(priv_pem, dh_secret)
    payload = dh_secret + b"::SIG::" + signature
    enc_sym_key, nonce, ciphertext, tag = hybrid_encrypt(recv_pub, payload)
    packet = {"type":"handshake","sender": identity,"enc_sym_key": b64encode(enc_sym_key).decode(),"nonce": b64encode(nonce).decode(),"ciphertext": b64encode(ciphertext).decode(),"tag": b64encode(tag).decode(),"ts": int(time.time())}
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((target_ip, target_port))
        send_msg(s, packet)
        s.close()
        print(f"[{identity}] Handshake sent to {receiver_id}")
        sym_key = SHA256.new(dh_secret).digest()
        toy_sym = gen_toy_symmetric_key(200,240)
        sessions[receiver_id] = {"sym_key": sym_key, "dh_secret": dh_secret, "msg_count": 0, "seen_ts": set(), "toy_sym": toy_sym}
        print(f"[{identity}] Toy symmetric key at sender (200-240 letters) sample: {toy_sym[:80]}... (len={len(toy_sym)})")
    except Exception as e:
        print(f"[{identity}] Error sending handshake: {e}")

def send_message_to_peer(identity, priv_pem, pub_pem, keydir, target_ip, target_port, recipient_id, plaintext):
    if recipient_id not in sessions:
        print(f"[{identity}] No session with {recipient_id}. Perform handshake first.")
        return
    sym_key = sessions[recipient_id]["sym_key"]
    plaintext_bytes = plaintext.encode()
    signature = rsa_sign(priv_pem, plaintext_bytes)
    nonce, ciphertext, tag = aes_gcm_encrypt(sym_key, plaintext_bytes)
    packet = {"type":"message","sender": identity,"recipient": recipient_id,"nonce": b64encode(nonce).decode(),"tag": b64encode(tag).decode(),"signature": b64encode(signature).decode(),"ciphertext": b64encode(ciphertext).decode(),"ts": int(time.time())}
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((target_ip, target_port))
        send_msg(s, packet)
        s.close()
        print(f"[{identity}] Encrypted & signed message sent to {recipient_id}")
    except Exception as e:
        print(f"[{identity}] Error sending message: {e}")

def send_close_notify(identity, priv_pem, pub_pem, keydir, target_ip, target_port, peer_id):
    sig = rsa_sign(priv_pem, b"CLOSE_SESSION")
    packet = {"type":"close_notify","sender": identity,"signature": b64encode(sig).decode(),"ts": int(time.time())}
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((target_ip, target_port))
        send_msg(s, packet)
        s.close()
        if peer_id in sessions: del sessions[peer_id]
        print(f"[{identity}] Sent close_notify to {peer_id}")
    except Exception as e:
        print(f"[{identity}] Error sending close_notify: {e}")

# ---------- chat helper ----------
def send_chat_message(identity, recipient_id, target_ip, target_port, plaintext):
    if recipient_id not in sessions:
        print(f"[{identity}] No session with {recipient_id}. Do handshake first.")
        return
    sess = sessions[recipient_id]
    nonce, ciphertext, tag = aes_gcm_encrypt(sess["sym_key"], plaintext.encode())
    packet = {
        "type": "chat",
        "sender": identity,
        "recipient": recipient_id,
        "nonce": b64encode(nonce).decode(),
        "ciphertext": b64encode(ciphertext).decode(),
        "tag": b64encode(tag).decode()
    }
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((target_ip, target_port))
        send_msg(s, packet)
        s.close()
    except Exception as e:
        print(f"[{identity}] Error sending chat: {e}")

# ---------- Crypto client menu ----------
def crypto_menu_loop():
    host = input("Crypto service host (default 127.0.0.1): ").strip() or "127.0.0.1"
    port = int(input("Crypto service port (default 6000): ").strip() or "6000")
    menu = """
Crypto Menu:
 1) AES Encryption
 2) AES Decryption
 3) RSA Encrypt
 4) RSA Decrypt
 5) Hybrid Encrypt (RSA(pub)+AES-GCM)
 6) Hybrid Decrypt
 7) Performance Comparison
 8) Back
Enter choice: """
    while True:
        choice = input(menu).strip()
        if choice == "1":
            mode = input("Mode (gcm/cbc) [gcm]: ").strip() or "gcm"
            use_key = input("Provide key? (y/N): ").strip().lower() == "y"
            key_b64 = ""
            iv_b64 = ""
            if use_key:
                key_hex = input("Enter key in hex (or leave blank): ").strip()
                if key_hex:
                    key_b64 = b64encode(bytes.fromhex(key_hex)).decode()
            if mode.lower() == "cbc":
                iv_hex = input("Enter IV in hex (or leave blank to generate): ").strip()
                if iv_hex:
                    iv_b64 = b64encode(bytes.fromhex(iv_hex)).decode()
            plaintext = input("Enter plaintext: ")
            req = {"cmd":"aes_enc","mode":mode,"key":key_b64,"iv":iv_b64,"plaintext": plaintext, "plain_b64": False}
            resp = crypto_request(host, port, req)
            print("Response:", resp)
        elif choice == "2":
            mode = input("Mode (gcm/cbc) [gcm]: ").strip() or "gcm"
            key_b64 = input("Enter key (base64): ").strip()
            if mode.lower() == "gcm":
                nonce_b64 = input("Enter nonce (base64): ").strip()
                ct_b64 = input("Enter ciphertext (base64): ").strip()
                tag_b64 = input("Enter tag (base64): ").strip()
                req = {"cmd":"aes_dec","mode":"gcm","key":key_b64,"nonce":nonce_b64,"ciphertext":ct_b64,"tag":tag_b64}
            else:
                iv_b64 = input("Enter IV (base64): ").strip()
                ct_b64 = input("Enter ciphertext (base64): ").strip()
                req = {"cmd":"aes_dec","mode":"cbc","key":key_b64,"iv":iv_b64,"ciphertext":ct_b64}
            resp = crypto_request(host, port, req)
            print("Response:", resp)
        elif choice == "3":
            pub_pem_path = input("Path to recipient public PEM (or paste PEM, leave blank to fetch from TPE): ").strip()
            if pub_pem_path and os.path.exists(pub_pem_path):
                pub_pem = open(pub_pem_path,"rb").read()
                pub_b64 = b64encode(pub_pem).decode()
            else:
                who = input("Enter recipient identity (for TPE fetch): ").strip()
                if who:
                    pub_pem = fetch_pub_from_tpe(who, ".", "local")
                    pub_b64 = b64encode(pub_pem).decode() if pub_pem else ""
                else:
                    pub_b64 = ""
            plaintext = input("Enter plaintext: ")
            req = {"cmd":"rsa_enc","pub":pub_b64,"plaintext": plaintext, "plain_b64": False}
            resp = crypto_request(host, port, req)
            print("Response:", resp)
        elif choice == "4":
            priv_path = input("Path to your private PEM: ").strip()
            if not priv_path or not os.path.exists(priv_path):
                print("Private PEM required to decrypt.")
                continue
            priv_pem = open(priv_path,"rb").read()
            ct_b64 = input("Enter ciphertext (base64): ").strip()
            req = {"cmd":"rsa_dec","priv": b64encode(priv_pem).decode(), "ciphertext": ct_b64}
            resp = crypto_request(host, port, req)
            print("Response:", resp)
        elif choice == "5":
            pub_pem_path = input("Path to recipient public PEM (or leave blank to fetch from TPE): ").strip()
            if pub_pem_path and os.path.exists(pub_pem_path):
                pub_pem = open(pub_pem_path,"rb").read()
                pub_b64 = b64encode(pub_pem).decode()
            else:
                who = input("Enter recipient identity (for TPE fetch): ").strip()
                pub_pem = fetch_pub_from_tpe(who, ".", "local")
                pub_b64 = b64encode(pub_pem).decode() if pub_pem else ""
            plaintext = input("Enter plaintext: ")
            req = {"cmd":"hybrid_enc","pub":pub_b64,"plaintext": plaintext, "plain_b64": False}
            resp = crypto_request(host, port, req)
            print("Response:", resp)
        elif choice == "6":
            priv_path = input("Path to your private PEM: ").strip()
            if not priv_path or not os.path.exists(priv_path):
                print("Private PEM required.")
                continue
            priv_pem = open(priv_path,"rb").read()
            enc_sym_key = input("Enter enc_sym_key (base64): ").strip()
            nonce = input("Enter nonce (base64): ").strip()
            ct = input("Enter ciphertext (base64): ").strip()
            tag = input("Enter tag (base64): ").strip()
            req = {"cmd":"hybrid_dec","priv": b64encode(priv_pem).decode(), "enc_sym_key": enc_sym_key, "nonce": nonce, "ciphertext": ct, "tag": tag}
            resp = crypto_request(host, port, req)
            print("Response:", resp)
        elif choice == "7":
            payload = input("Payload to use for timing (short/long text): ")
            use_keys = input("Use RSA keypair for RSA/hybrid timing? (y/N): ").strip().lower() == "y"
            pub_b64 = priv_b64 = ""
            if use_keys:
                priv_path = input("Path to your private PEM: ").strip()
                pub_path = input("Path to your public PEM: ").strip()
                if os.path.exists(priv_path) and os.path.exists(pub_path):
                    priv_b64 = b64encode(open(priv_path,"rb").read()).decode()
                    pub_b64 = b64encode(open(pub_path,"rb").read()).decode()
            req = {"cmd":"perf_compare","payload": payload, "payload_b64": False, "pub": pub_b64, "priv": priv_b64}
            resp = crypto_request(host, port, req, timeout=30)
            print("Timing response:", resp)
        elif choice == "8":
            break
        else:
            print("Invalid option.")

# ---------- interactive menu ----------
def interactive_loop(identity, priv_pem, pub_pem, keydir, listen_host, listen_port):
    print(f"\n[{identity}] Interactive menu. TPE={TPE_HOST}:{TPE_PORT}. Your server at {listen_host}:{listen_port}\n")
    menu = """
Choose action:
 1) Crypto client menu (AES/RSA/Hybrid/Perf)
 2) Register public key with TPE
 3) Fetch someone's public key from TPE (and store locally)
 4) Initiate SSL-1 handshake (connect to peer IP:port)
 5) Send encrypted & signed message (connect to peer IP:port)
 6) Send close_notify
 7) Start chat with peer (quick interactive)
 8) List local state (keyring, sessions)
 9) Exit
Enter choice: """
    while True:
        choice = input(menu).strip()
        if choice == "1":
            crypto_menu_loop()
        elif choice == "2":
            register_with_tpe(identity, pub_pem)
        elif choice == "3":
            other = input("Enter identity to fetch public key for: ").strip()
            if other:
                get_pubkey(other, keydir, identity)
        elif choice == "4":
            receiver_id = input("Enter receiver identity: ").strip()
            target_ip = input("Enter receiver IP/hostname: ").strip()
            target_port = int(input("Enter receiver port: ").strip())
            send_handshake_to_peer(identity, priv_pem, pub_pem, keydir, target_ip, target_port, receiver_id)
        elif choice == "5":
            recipient_id = input("Enter recipient identity: ").strip()
            target_ip = input("Enter recipient IP/hostname: ").strip()
            target_port = int(input("Enter recipient port: ").strip())
            plaintext = input("Enter plaintext message to send: ")
            send_message_to_peer(identity, priv_pem, pub_pem, keydir, target_ip, target_port, recipient_id, plaintext)
        elif choice == "6":
            peer_id = input("Enter peer identity: ").strip()
            target_ip = input("Enter peer IP/hostname: ").strip()
            target_port = int(input("Enter peer port: ").strip())
            send_close_notify(identity, priv_pem, pub_pem, keydir, target_ip, target_port, peer_id)
        elif choice == "7":
            peer_id = input("Enter peer identity: ").strip()
            target_ip = input("Enter peer IP/hostname: ").strip()
            target_port = int(input("Enter peer base port: ").strip())
            print("Enter messages (type /exit to quit chat):")
            while True:
                msg = input("> ")
                if msg.strip() == "/exit":
                    break
                send_chat_message(identity, peer_id, target_ip, target_port, msg)
        elif choice == "8":
            kr = {}
            kr_path = os.path.join(keydir, "keyring.json")
            if os.path.exists(kr_path):
                kr = json.load(open(kr_path, "r"))
            print(f"[{identity}] Local keyring entries: {list(kr.keys())}")
            print(f"[{identity}] Active sessions: {list(sessions.keys())}")
        elif choice == "9":
            print("Exiting.")
            break
        else:
            print("Invalid option.")

if __name__ == "__main__":
    identity = input("Enter your identity (Alice/Bob/Charlie/David or any name): ").strip()
    if not identity:
        print("Identity required. Exiting.")
        exit(1)
    listen_host = input("Enter IP to listen on (default 0.0.0.0): ").strip() or "0.0.0.0"
    listen_port = int(input("Enter port to listen on (e.g. 7000): ").strip() or "7000")
    priv_pem, pub_pem, keydir = ensure_keys(identity)
    start_peer_server(identity, priv_pem, pub_pem, keydir, listen_host, listen_port)
    interactive_loop(identity, priv_pem, pub_pem, keydir, listen_host, listen_port)
