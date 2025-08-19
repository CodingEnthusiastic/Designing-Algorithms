import socket
import threading
import logging
import os   # for os._exit

HOST = "localhost"
PORT = 5005

# Sample data: shops and their inventory
SHOP_INVENTORY = {
    'ShopA': {'Apple': 10, 'Banana': 5, 'Orange': 3},
    'ShopB': {'Banana': 15, 'Milk': 8, 'Bread': 2},
    'ShopC': {'Apple': 3, 'Orange': 6, 'Bread': 0},
}

inventory_lock = threading.Lock()

logging.basicConfig(
    filename="server.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class ClientHandler(threading.Thread):
    def __init__(self, client_socket, shop_inventory):
        super().__init__(daemon=True)
        self.client_socket = client_socket
        self.shop_inventory = shop_inventory

    def run(self):
        try:
            while True:
                data = self.client_socket.recv(1024)
                if not data:
                    break
                query = data.decode(errors="ignore").strip()
                if not query or query.lower() == "exit":
                    break
                logging.info(f"Received query: {query}")
                response = self.process_query(query)
                self.client_socket.sendall(response.encode())
        except ConnectionResetError:
            logging.warning("Client disconnected abruptly.")
        except Exception as e:
            logging.error(f"Error: {e}")
        finally:
            self.client_socket.close()

    # ---------- Helpers ----------
    def _find_shop_key(self, name: str):
        """Return the exact dict key for a shop name (case-insensitive), else None."""
        target = name.casefold()
        for shop in self.shop_inventory.keys():
            if shop.casefold() == target:
                return shop
        return None

    def _find_item_key(self, shop: str, item: str):
        """Return the exact dict key for an item name in a shop (case-insensitive), else None."""
        target = item.casefold()
        for key in self.shop_inventory[shop].keys():
            if key.casefold() == target:
                return key
        return None

    # ---------- Core ----------
    def process_query(self, query):
        tokens = query.split()
        if not tokens:
            return "Invalid query."

        # Shutdown command
        if query.lower() == "shutdown":
            logging.info("Shutdown command received. Closing server.")
            self.client_socket.sendall("🛑 Server is shutting down...".encode())
            os._exit(0)  # immediately kill server + threads

        # Support: buy <item> <shop>
        if tokens[0].lower() == "buy" and len(tokens) >= 3:
            item = tokens[1]
            shop = " ".join(tokens[2:])
            return self.handle_purchase(item, shop)

        # Check if query is a shop name (case-insensitive)
        shop_key = self._find_shop_key(query)
        if shop_key:
            items = self.shop_inventory[shop_key]
            items_list = [f"{name}: {qty}" for name, qty in items.items() if qty > 0]
            return (
                f"Items in {shop_key}: " + ", ".join(items_list)
                if items_list
                else f"No items available in {shop_key}."
            )

        # Otherwise treat it as an item search (case-insensitive)
        q_cf = query.casefold()
        shops_with_item = []
        for shop, items in self.shop_inventory.items():
            for item, qty in items.items():
                if item.casefold() == q_cf and qty > 0:
                    shops_with_item.append(f"{shop} (Qty: {qty})")
        return (
            f"{query} is available in: " + ", ".join(shops_with_item)
            if shops_with_item
            else f"{query} is NOT available in any local shop."
        )

    def handle_purchase(self, item, shop):
        shop_key = self._find_shop_key(shop)
        if not shop_key:
            return f"Shop {shop} does not exist."

        with inventory_lock:
            item_key = self._find_item_key(shop_key, item)
            if item_key and self.shop_inventory[shop_key][item_key] > 0:
                self.shop_inventory[shop_key][item_key] -= 1
                return (
                    f"✅ Successfully purchased 1 {item_key} from {shop_key}. "
                    f"Remaining: {self.shop_inventory[shop_key][item_key]}"
                )
            else:
                return f"❌ {item} is not available in {shop_key}."


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"🛒 Store Server running on {HOST}:{PORT}...")
    logging.info("Server started.")

    try:
        while True:
            client_sock, addr = server_socket.accept()
            print(f"🔗 Connection from {addr}")
            handler = ClientHandler(client_sock, SHOP_INVENTORY)
            handler.start()
    except KeyboardInterrupt:
        print("\n🛑 Server shutting down (via Ctrl+C)...")
        logging.info("Server stopped.")
    finally:
        server_socket.close()

if __name__ == "__main__":
    main()
