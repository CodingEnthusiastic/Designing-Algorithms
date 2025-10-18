def check_crl(serial_number):
    revoked_list = ["1002", "1005"]
    if serial_number in revoked_list:
        return "revoked"
    else:
        return "good"

if __name__ == "__main__":
    serial = input("Enter certificate serial number for CRL check: ")
    print(f"CRL Status for {serial}: {check_crl(serial)}")
