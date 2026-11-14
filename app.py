import json
import sqlite3
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


APP_DIR = Path(__file__).resolve().parent
DATABASE = APP_DIR / "food_cart_orders.sqlite3"
HOST = "127.0.0.1"
PORT = 8000
ORDER_STATUSES = ("received", "preparing", "ready", "completed")

CARTS = [
    {
        "id": "shawarma-chef",
        "name": "Shawarma Chef",
        "cuisine": "Middle Eastern",
        "description": "Middle Eastern favorites, made fresh.",
        "time": "10–15 min",
        "color": "#c68b4b",
        "icon": "🥙",
        "items": [
            ("shawarma-chicken-wrap", "Chicken shawarma wrap", "Seasoned chicken, fresh vegetables & house sauce.", 1350, "🥙", "Popular"),
            ("shawarma-falafel-plate", "Falafel plate", "Crisp falafel served with hummus and pita.", 1250, "🧆", "Vegetarian"),
            ("shawarma-hummus", "Hummus & pita", "Creamy hummus with warm pita bread.", 750, "🫓", ""),
            ("shawarma-mint-lemonade", "Mint lemonade", "Lemonade with a hint of fresh mint.", 450, "🍋", "Cold drink"),
        ],
    },
    {
        "id": "e-san-thai",
        "name": "E-San Thai Cuisine",
        "cuisine": "Thai",
        "description": "Thai comfort food, prepared to order.",
        "time": "12–18 min",
        "color": "#c86c56",
        "icon": "🍜",
        "items": [
            ("esan-pad-thai", "Pad Thai", "Rice noodles, vegetables, egg & roasted peanuts.", 1450, "🍜", "Popular"),
            ("esan-green-curry", "Green curry", "A fragrant coconut curry with seasonal vegetables.", 1550, "🍛", ""),
            ("esan-spring-rolls", "Fresh spring rolls", "Vegetables and herbs wrapped with a dipping sauce.", 800, "🥢", "Vegetarian"),
            ("esan-thai-iced-tea", "Thai iced tea", "Sweet Thai tea served over ice.", 500, "🧋", "Cold drink"),
        ],
    },
    {
        "id": "Gothic-Bites",
        "name": "Gothic Bites",
        "cuisine": "Asian",
        "description": "Fresh Asian-inspired favorites.",
        "time": "8–12 min",
        "color": "#78a16e",
        "icon": "🐼",
        "items": [
            ("healthy-teriyaki-bowl", "Teriyaki bowl", "A warm rice bowl with vegetables and teriyaki sauce.", 1350, "🍱", "Popular"),
            ("healthy-orange-chicken", "Orange chicken", "Crispy chicken with a bright orange glaze.", 1450, "🍊", ""),
            ("healthy-veggie-rolls", "Vegetable rolls", "Crisp vegetables with a savory dipping sauce.", 800, "🥢", "Vegetarian"),
            ("healthy-boba-tea", "Milk tea", "Chilled milk tea with chewy tapioca pearls.", 550, "🧋", "Cold drink"),
        ],
    },
    {
        "id": "el-punto-venezolano",
        "name": "El Punto Venezolano",
        "cuisine": "Venezuelan",
        "description": "Venezuelan specialties, full of flavor.",
        "time": "10–14 min",
        "color": "#e0aa43",
        "icon": "🫓",
        "items": [
            ("punto-reina-pepiada", "Reina pepiada arepa", "Corn arepa filled with chicken and avocado.", 1350, "🫓", "Popular"),
            ("punto-pabellon", "Pabellón bowl", "Rice, black beans, plantain and shredded beef.", 1550, "🍛", ""),
            ("punto-empanadas", "Venezuelan empanadas", "Golden corn pockets with a savory filling.", 900, "🥟", ""),
            ("punto-papelon", "Papelón con limón", "A refreshing cane sugar and lime drink.", 500, "🍋", "Cold drink"),
        ],
    },
    {
        "id": "xanos-mexican-food",
        "name": "Xanos Mexican Food",
        "cuisine": "Mexican",
        "description": "Mexican favorites, made fresh.",
        "time": "10–15 min",
        "color": "#f0a548",
        "icon": "🌮",
        "items": [
            ("xanos-street-tacos", "Street tacos", "Three grilled steak tacos, salsa verde, cilantro & lime.", 1250, "🌮", "Popular"),
            ("xanos-quesadilla", "Crunchy quesadilla", "Golden flour tortilla, Oaxaca cheese & chipotle crema.", 1100, "🫓", ""),
            ("xanos-loaded-nachos", "Loaded nachos", "Crispy chips, black beans, queso, pico & guacamole.", 1350, "🧀", "Vegetarian"),
            ("xanos-agua-fresca", "Watermelon agua fresca", "Fresh watermelon, lime & a little sparkle.", 450, "🍉", "Cold drink"),
        ],
    },
]


@contextmanager
def connect_database():
    connection = sqlite3.connect(DATABASE, timeout=10)
    try:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        with connection:
            yield connection
    finally:
        connection.close()


def initialize_database():
    with connect_database() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS carts (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                cuisine TEXT NOT NULL,
                description TEXT NOT NULL,
                pickup_time TEXT NOT NULL,
                color TEXT NOT NULL,
                icon TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS menu_items (
                id TEXT PRIMARY KEY,
                cart_id TEXT NOT NULL REFERENCES carts(id),
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                price_cents INTEGER NOT NULL CHECK (price_cents >= 0),
                icon TEXT NOT NULL,
                badge TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cart_id TEXT NOT NULL REFERENCES carts(id),
                customer_name TEXT NOT NULL,
                pickup_code TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL DEFAULT 'received'
                    CHECK (status IN ('received', 'preparing', 'ready', 'completed')),
                total_cents INTEGER NOT NULL CHECK (total_cents > 0),
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
                menu_item_id TEXT NOT NULL REFERENCES menu_items(id),
                item_name TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity BETWEEN 1 AND 20),
                unit_price_cents INTEGER NOT NULL CHECK (unit_price_cents >= 0)
            );
            CREATE INDEX IF NOT EXISTS orders_cart_status_created
                ON orders(cart_id, status, created_at);
            """
        )
        for cart in CARTS:
            connection.execute(
                """
                INSERT OR IGNORE INTO carts
                    (id, name, cuisine, description, pickup_time, color, icon)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (cart["id"], cart["name"], cart["cuisine"], cart["description"],
                 cart["time"], cart["color"], cart["icon"]),
            )
            for item in cart["items"]:
                item_id, name, description, price, icon, badge = item
                connection.execute(
                    """
                    INSERT OR IGNORE INTO menu_items
                        (id, cart_id, name, description, price_cents, icon, badge)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (item_id, cart["id"], name, description, price, icon, badge),
                )


class RequestHandler(BaseHTTPRequestHandler):
    server_version = "Cartside/1.0"

    def send_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length < 1 or length > 16_384:
            raise ValueError("Request body must be under 16 KB.")
        return json.loads(self.rfile.read(length))

    def do_GET(self):
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        try:
            if parsed.path == "/api/carts":
                with connect_database() as connection:
                    carts = connection.execute(
                        """
                        SELECT c.*,
                            (SELECT COUNT(*) FROM menu_items m WHERE m.cart_id = c.id) AS item_count
                        FROM carts c WHERE c.id IN (""" + ", ".join("?" for _ in CARTS) + ") ORDER BY c.name",
                        [cart["id"] for cart in CARTS],
                    ).fetchall()
                    result = []
                    for cart in carts:
                        data = dict(cart)
                        data["items"] = [
                            dict(item) for item in connection.execute(
                                "SELECT * FROM menu_items WHERE cart_id = ? ORDER BY name",
                                (cart["id"],),
                            ).fetchall()
                        ]
                        result.append(data)
                self.send_json({"carts": result})
                return

            if parsed.path == "/api/orders":
                cart_id = query.get("cart_id", [None])[0]
                status = query.get("status", [None])[0]
                conditions = []
                values = []
                if cart_id:
                    conditions.append("o.cart_id = ?")
                    values.append(cart_id)
                if status:
                    if status not in ORDER_STATUSES:
                        self.send_json({"error": "Unknown order status."}, 400)
                        return
                    conditions.append("o.status = ?")
                    values.append(status)
                where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
                with connect_database() as connection:
                    rows = connection.execute(
                        """
                        SELECT o.*, c.name AS cart_name, c.icon AS cart_icon
                        FROM orders o JOIN carts c ON c.id = o.cart_id
                        """
                        + where_clause
                        + " ORDER BY o.created_at DESC, o.id DESC LIMIT 100",
                        values,
                    ).fetchall()
                    orders = []
                    for row in rows:
                        order = dict(row)
                        order["items"] = [
                            dict(item) for item in connection.execute(
                                """
                                SELECT item_name AS name, quantity, unit_price_cents
                                FROM order_items WHERE order_id = ? ORDER BY id
                                """,
                                (order["id"],),
                            ).fetchall()
                        ]
                        orders.append(order)
                self.send_json({"orders": orders})
                return

            if parsed.path.startswith("/api/"):
                self.send_json({"error": "API endpoint not found."}, 404)
                return

            if parsed.path in ("/", "/index.html", "/app.js", "/styles.css"):
                file_name = "index.html" if parsed.path == "/" else parsed.path.lstrip("/")
                content_type = "text/html; charset=utf-8" if file_name.endswith(".html") else "text/javascript; charset=utf-8" if file_name.endswith(".js") else "text/css; charset=utf-8"
                body = (APP_DIR / file_name).read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            self.send_json({"error": "Not found."}, 404)
        except (sqlite3.Error, OSError) as error:
            print(f"Request failed: {error}")
            self.send_json({"error": "The request could not be completed. Please try again."}, 500)

    def do_POST(self):
        if urlparse(self.path).path != "/api/orders":
            self.send_json({"error": "API endpoint not found."}, 404)
            return
        try:
            data = self.read_json()
            if not isinstance(data, dict):
                self.send_json({"error": "Order details must be sent as an object."}, 400)
                return
            customer_name = data.get("customer_name", "").strip()
            cart_id = data.get("cart_id")
            items = data.get("items")
            if not isinstance(customer_name, str) or not 1 <= len(customer_name) <= 60:
                self.send_json({"error": "Please enter a name between 1 and 60 characters."}, 400)
                return
            if not isinstance(cart_id, str) or not isinstance(items, list) or not 1 <= len(items) <= 30:
                self.send_json({"error": "Choose a cart and add at least one menu item."}, 400)
                return

            quantities = {}
            for item in items:
                if not isinstance(item, dict):
                    self.send_json({"error": "Order items are invalid."}, 400)
                    return
                item_id = item.get("menu_item_id")
                quantity = item.get("quantity")
                if (
                    not isinstance(item_id, str)
                    or not isinstance(quantity, int)
                    or isinstance(quantity, bool)
                    or not 1 <= quantity <= 20
                ):
                    self.send_json({"error": "Each quantity must be between 1 and 20."}, 400)
                    return
                quantities[item_id] = quantities.get(item_id, 0) + quantity
                if quantities[item_id] > 20:
                    self.send_json({"error": "Each item is limited to 20 per order."}, 400)
                    return

            with connect_database() as connection:
                menu = connection.execute(
                    "SELECT id, name, price_cents FROM menu_items WHERE cart_id = ?",
                    (cart_id,),
                ).fetchall()
                menu_by_id = {item["id"]: item for item in menu}
                if not menu_by_id:
                    self.send_json({"error": "That food cart could not be found."}, 404)
                    return
                if any(item_id not in menu_by_id for item_id in quantities):
                    self.send_json({"error": "All items in an order must come from the same food cart."}, 400)
                    return

                total_cents = sum(
                    menu_by_id[item_id]["price_cents"] * quantity
                    for item_id, quantity in quantities.items()
                )
                cursor = connection.execute(
                    """
                    INSERT INTO orders (cart_id, customer_name, pickup_code, total_cents)
                    VALUES (?, ?, 'PENDING', ?)
                    """,
                    (cart_id, customer_name, total_cents),
                )
                order_id = cursor.lastrowid
                pickup_code = f"{order_id:03d}"
                connection.execute(
                    "UPDATE orders SET pickup_code = ? WHERE id = ?",
                    (pickup_code, order_id),
                )
                for item_id, quantity in quantities.items():
                    item = menu_by_id[item_id]
                    connection.execute(
                        """
                        INSERT INTO order_items
                            (order_id, menu_item_id, item_name, quantity, unit_price_cents)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (order_id, item_id, item["name"], quantity, item["price_cents"]),
                    )

            self.send_json(
                {
                    "order_id": order_id,
                    "pickup_code": pickup_code,
                    "cart_id": cart_id,
                    "total_cents": total_cents,
                },
                201,
            )
        except (ValueError, json.JSONDecodeError) as error:
            self.send_json({"error": str(error) or "Invalid request."}, 400)
        except sqlite3.Error as error:
            print(f"Order could not be saved: {error}")
            self.send_json({"error": "Your order could not be saved. Please try again."}, 500)

    def do_PATCH(self):
        parts = urlparse(self.path).path.strip("/").split("/")
        if len(parts) != 4 or parts[:2] != ["api", "orders"] or parts[3] != "status":
            self.send_json({"error": "API endpoint not found."}, 404)
            return
        try:
            order_id = int(parts[2])
            data = self.read_json()
            if not isinstance(data, dict):
                self.send_json({"error": "Order status must be sent as an object."}, 400)
                return
            status = data.get("status")
            if status not in ORDER_STATUSES:
                self.send_json({"error": "Choose a valid order status."}, 400)
                return
            with connect_database() as connection:
                cursor = connection.execute(
                    "UPDATE orders SET status = ? WHERE id = ?",
                    (status, order_id),
                )
                if cursor.rowcount == 0:
                    self.send_json({"error": "Order not found."}, 404)
                    return
            self.send_json({"ok": True})
        except (ValueError, json.JSONDecodeError) as error:
            self.send_json({"error": str(error) or "Invalid request."}, 400)
        except sqlite3.Error as error:
            print(f"Order status could not be updated: {error}")
            self.send_json({"error": "Order status could not be updated. Please try again."}, 500)

    def log_message(self, format_string, *args):
        print(f"{self.address_string()} - {format_string % args}")


if __name__ == "__main__":
    initialize_database()
    server = ThreadingHTTPServer((HOST, PORT), RequestHandler)
    print(f"Cartside is running at http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Cartside.")
        server.server_close()
