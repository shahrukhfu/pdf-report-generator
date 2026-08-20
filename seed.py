import sqlite3
import random
from datetime import datetime, timedelta

DB_NAME = "report.db"

CUSTOMERS = [
    "Alice Smith", "Bob Jones", "Charlie Brown", "Diana Prince",
    "Evan Wright", "Fiona Gallagher", "George Clark", "Hannah Abbott",
    "Ian Malcolm", "Julia Roberts", "Kevin Bacon", "Laura Croft"
]

PRODUCTS = [
    "Wireless Mouse",
    "Mechanical Keyboard",
    "USB-C Hub",
    "HD Monitor",
    "Noise-Canceling Headphones",
    "Ergonomic Mousepad"
]

def seed_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Create table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer TEXT,
            product TEXT,
            amount REAL,
            created_at TEXT
        )
    """)

    # Delete existing rows to ensure idempotency
    cursor.execute("DELETE FROM orders")

    now = datetime.now()
    orders_data = []

    for _ in range(200):
        customer = random.choice(CUSTOMERS)
        product = random.choice(PRODUCTS)
        amount = round(random.uniform(5.0, 200.0), 2)
        
        # Random timestamp spanning the last 30 days
        random_days = random.uniform(0, 30)
        timestamp = (now - timedelta(days=random_days)).strftime("%Y-%m-%d %H:%M:%S")
        
        orders_data.append((customer, product, amount, timestamp))

    cursor.executemany("""
        INSERT INTO orders (customer, product, amount, created_at)
        VALUES (?, ?, ?, ?)
    """, orders_data)

    conn.commit()

    # Verification query
    cursor.execute("SELECT COUNT(*) FROM orders")
    count = cursor.fetchone()[0]
    print(f"Total orders in database: {count}")

    conn.close()

if __name__ == "__main__":
    # Seed with fixed random seed if needed, but standard seed function suffices
    random.seed(42)
    seed_database()
