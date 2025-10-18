import os, json, datetime, hashlib
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.x509.oid import NameOID, ExtensionOID

DB_FILE = "cert_db.json"

# -------------------- Utility functions --------------------
def load_cert(path):
    with open(path, "rb") as f:
        data = f.read()
    try:
        return x509.load_pem_x509_certificate(data)
    except Exception:
        return x509.load_der_x509_certificate(data)

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)

def load_db():
    if not os.path.exists(DB_FILE):
        return {"serials": {}, "revoked": {}}
    with open(DB_FILE) as f:
        return json.load(f)

# -------------------- Parser --------------------
def parse_menu():
    path = input("Enter certificate path (PEM/DER): ").strip()
    try:
        cert = load_cert(path)
    except Exception as e:
        print("Error loading:", e)
        return

    print("\n--- Parsed Certificate ---")
    print("Version:", cert.version.name)
    print("Serial Number:", hex(cert.serial_number))
    print("Signature Algorithm:", cert.signature_algorithm_oid._name)
    print("Issuer:", cert.issuer.rfc4514_string())
    print("Subject:", cert.subject.rfc4514_string())
    print("Validity:")
    print("  Not Before:", cert.not_valid_before)
    print("  Not After :", cert.not_valid_after)

    pubkey = cert.public_key()
    if isinstance(pubkey, rsa.RSAPublicKey):
        numbers = pubkey.public_numbers()
        print("Public Key Algorithm: RSA")
        print("  Modulus bits:", pubkey.key_size)
        print("  Exponent:", numbers.e)
    else:
        print("Public Key Type:", type(pubkey).__name__)

    print("\nExtensions:")
    for ext in cert.extensions:
        print(f"  {ext.oid._name}: {ext.value}")

    der_bytes = cert.public_bytes(serialization.Encoding.DER)
    sha1 = hashlib.sha1(der_bytes).hexdigest()
    sha256 = hashlib.sha256(der_bytes).hexdigest()
    print("\nFingerprint (SHA1):", sha1)
    print("Fingerprint (SHA256):", sha256)

# -------------------- Chain Validation --------------------
def verify_signature(child, issuer_cert):
    issuer_pub = issuer_cert.public_key()
    try:
        issuer_pub.verify(
            child.signature,
            child.tbs_certificate_bytes,
            padding.PKCS1v15(),
            child.signature_hash_algorithm,
        )
        return True
    except Exception as e:
        print("Signature verification failed:", e)
        return False

def chain_menu():
    end_path = input("Enter end-entity cert path: ").strip()
    inter_path = input("Enter intermediate cert path: ").strip()
    root_path = input("Enter root cert path: ").strip()
    try:
        end = load_cert(end_path)
        inter = load_cert(inter_path)
        root = load_cert(root_path)
    except Exception as e:
        print("Error loading:", e)
        return

    print("\n--- Certificate Chain Validation ---")
    ok = True

    if end.issuer != inter.subject:
        print("End certificate issuer mismatch.")
        ok = False
    if inter.issuer != root.subject:
        print("Intermediate issuer mismatch.")
        ok = False

    if not verify_signature(end, inter):
        ok = False
    if not verify_signature(inter, root):
        ok = False

    now = datetime.datetime.utcnow()
    for c, name in [(end,"End"), (inter,"Intermediate"), (root,"Root")]:
        if not (c.not_valid_before <= now <= c.not_valid_after):
            print(f"{name} certificate expired or not yet valid.")
            ok = False

    try:
        bc = inter.extensions.get_extension_for_oid(ExtensionOID.BASIC_CONSTRAINTS).value
        if not bc.ca:
            print("Intermediate not marked as CA!")
            ok = False
    except Exception:
        print("No BasicConstraints found on intermediate")

    print("\nChain Validation:", "SUCCESS ✅" if ok else "FAILED ❌")

# -------------------- CA Operations --------------------
def create_root_ca():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "IN"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SPIT"),
        x509.NameAttribute(NameOID.COMMON_NAME, "Test Root CA")
    ])
    cert = (x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.utcnow())
            .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=3650))
            .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
            .sign(key, hashes.SHA256()))
    os.makedirs("test_certs", exist_ok=True)
    with open("test_certs/ca.key.pem","wb") as f:
        f.write(key.private_bytes(serialization.Encoding.PEM,
                                  serialization.PrivateFormat.TraditionalOpenSSL,
                                  serialization.NoEncryption()))
    with open("test_certs/ca.cert.pem","wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    print("Root CA generated → test_certs/ca.cert.pem")

def issue_cert(cn):
    db = load_db()
    with open("test_certs/ca.key.pem","rb") as f:
        ca_key = serialization.load_pem_private_key(f.read(), password=None)
    ca_cert = load_cert("test_certs/ca.cert.pem")
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, cn)])
    cert = (x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(ca_cert.subject)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.utcnow())
            .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .sign(ca_key, hashes.SHA256()))
    path = f"test_certs/{cn}.cert.pem"
    with open(path,"wb") as f: f.write(cert.public_bytes(serialization.Encoding.PEM))
    with open(f"test_certs/{cn}.key.pem","wb") as f:
        f.write(key.private_bytes(serialization.Encoding.PEM,
                                  serialization.PrivateFormat.TraditionalOpenSSL,
                                  serialization.NoEncryption()))
    db["serials"][hex(cert.serial_number)] = {"cn": cn, "status":"valid"}
    save_db(db)
    print(f"Issued certificate for {cn} → {path}")

def revoke_cert(serial):
    db = load_db()
    if serial in db["serials"]:
        db["revoked"][serial] = str(datetime.datetime.utcnow())
        db["serials"][serial]["status"] = "revoked"
        save_db(db)
        print(f"Serial {serial} revoked.")
    else:
        print("Serial not found.")

def ca_menu():
    print("\n1. Generate Root CA\n2. Issue Certificate\n3. Revoke Certificate")
    op = input("Enter option: ")
    if op == "1": create_root_ca()
    elif op == "2":
        cn = input("Enter Common Name for new cert: ")
        issue_cert(cn)
    elif op == "3":
        serial = input("Enter serial (hex) to revoke: ")
        revoke_cert(serial)

# -------------------- Status Check --------------------
def status_menu():
    serial = input("Enter certificate serial (hex): ")
    db = load_db()
    if serial in db["revoked"]:
        print("Status: REVOKED at", db["revoked"][serial])
    elif serial in db["serials"]:
        print("Status:", db["serials"][serial]["status"])
    else:
        print("Serial not found.")

# -------------------- Main Menu --------------------
def main():
    while True:
        print("\n--- X.509 PKI MENU ---")
        print("1. Parse Certificate")
        print("2. Verify Certificate Chain")
        print("3. CA Operations (Issue/Revoke)")
        print("4. Certificate Status Check")
        print("5. Quit")
        ch = input("Enter choice: ")
        if ch == "1": parse_menu()
        elif ch == "2": chain_menu()
        elif ch == "3": ca_menu()
        elif ch == "4": status_menu()
        elif ch == "5": break
        else: print("Invalid option")

if __name__ == "__main__":
    main()
