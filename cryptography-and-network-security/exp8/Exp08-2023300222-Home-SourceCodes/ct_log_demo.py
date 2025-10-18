import json
import time

def log_certificate(cert_name):
    log_entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "certificate": cert_name
    }

    with open("ct_log.json", "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    print(f"✅ Certificate '{cert_name}' logged to CT log.")

if __name__ == "__main__":
    cert_name = input("Enter certificate name to log: ")
    log_certificate(cert_name)
