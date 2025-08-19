import socket

HOST = "localhost"
PORT = 5005

def client():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))
        print("✅ Connected to Marketplace Server")
        print("Type 'exit' to quit.")
        print("Commands: \n - Search by shop/item name\n - buy <item> <shop> to purchase")

        while True:
            query = input("\nEnter query: ").strip()
            if not query:
                continue
            if query.lower() == "exit":
                sock.sendall(query.encode())
                break

            sock.sendall(query.encode())
            response = sock.recv(4096).decode()
            print(f"📌 {response}")

    except ConnectionRefusedError:
        print("❌ Could not connect to server. Is it running?")
    except Exception as e:
        print(f"⚠ Error: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    client()
