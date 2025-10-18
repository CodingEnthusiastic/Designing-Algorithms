import json
import requests

def query_ocsp(serial_number):
    url = "http://127.0.0.1:8000/ocsp"
    data = {"serial_number": serial_number}
    response = requests.post(url, json=data)
    if response.status_code == 200:
        print("OCSP Response:", response.json())
    else:
        print("Error:", response.status_code)

if __name__ == "__main__":
    serial_number = input("Enter certificate serial number: ")
    query_ocsp(serial_number)
