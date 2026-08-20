import sqlite3
import json

DB_NAME = "report.db"

def get_report_data(db_path: str = DB_NAME) -> dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Total Orders
    cursor.execute("SELECT COUNT(*) AS total_orders FROM orders;")
    total_orders = cursor.fetchone()["total_orders"] or 0

    # 2. Total Revenue
    cursor.execute("SELECT SUM(amount) AS total_revenue FROM orders;")
    total_revenue_raw = cursor.fetchone()["total_revenue"]
    total_revenue = round(total_revenue_raw, 2) if total_revenue_raw is not None else 0.0

    # 3. Top 5 Products by Revenue
    cursor.execute("""
        SELECT product, SUM(amount) AS total_sales, COUNT(*) AS count 
        FROM orders 
        GROUP BY product 
        ORDER BY total_sales DESC 
        LIMIT 5;
    """)
    top_products = [
        {
            "product": row["product"],
            "total_sales": round(row["total_sales"], 2) if row["total_sales"] is not None else 0.0,
            "count": row["count"]
        }
        for row in cursor.fetchall()
    ]

    # 4. Daily Orders (Last 7 Days)
    cursor.execute("""
        SELECT date(created_at) AS day, COUNT(*) AS order_count, SUM(amount) AS daily_revenue 
        FROM orders 
        GROUP BY date(created_at) 
        ORDER BY day DESC 
        LIMIT 7;
    """)
    daily_orders = [
        {
            "day": row["day"],
            "order_count": row["order_count"],
            "daily_revenue": round(row["daily_revenue"], 2) if row["daily_revenue"] is not None else 0.0
        }
        for row in cursor.fetchall()
    ]

    # 5. Raw Orders (all rows for detailed table)
    cursor.execute("SELECT id, customer, product, amount, created_at FROM orders ORDER BY id ASC;")
    raw_orders = [
        {
            "id": row["id"],
            "customer": row["customer"],
            "product": row["product"],
            "amount": round(row["amount"], 2),
            "created_at": row["created_at"]
        }
        for row in cursor.fetchall()
    ]

    conn.close()

    return {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "top_products": top_products,
        "daily_orders": daily_orders,
        "raw_orders": raw_orders
    }

if __name__ == "__main__":
    data = get_report_data()
    # Print formatted JSON (excluding raw_orders in preview or printing summary length if too long, or printing standard json)
    preview_data = {
        "total_orders": data["total_orders"],
        "total_revenue": data["total_revenue"],
        "top_products": data["top_products"],
        "daily_orders": data["daily_orders"],
        "raw_orders_count": len(data["raw_orders"]),
        "sample_raw_orders": data["raw_orders"][:3]
    }
    print(json.dumps(preview_data, indent=2))
