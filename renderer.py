import asyncio
import os
from datetime import datetime
from playwright.async_api import async_playwright
from report_data import get_report_data

def generate_report_html(data: dict) -> str:
    timestamp_str = datetime.now().strftime("%B %d, %Y - %H:%M:%S")
    
    total_orders = data.get("total_orders", 0)
    total_revenue = f"${data.get('total_revenue', 0.0):,.2f}"

    # Top products table rows
    top_products_rows = ""
    for prod in data.get("top_products", []):
        sales = f"${prod['total_sales']:,.2f}"
        top_products_rows += f"""
        <tr>
            <td>{prod['product']}</td>
            <td style="text-align: right;">{sales}</td>
            <td style="text-align: right;">{prod['count']}</td>
        </tr>
        """

    # Daily orders table rows
    daily_orders_rows = ""
    for day_item in data.get("daily_orders", []):
        rev = f"${day_item['daily_revenue']:,.2f}"
        daily_orders_rows += f"""
        <tr>
            <td>{day_item['day']}</td>
            <td style="text-align: right;">{day_item['order_count']}</td>
            <td style="text-align: right;">{rev}</td>
        </tr>
        """

    # Raw orders table rows (~200 rows)
    raw_orders_rows = ""
    for order in data.get("raw_orders", []):
        amt = f"${order['amount']:,.2f}"
        raw_orders_rows += f"""
        <tr>
            <td>#{order['id']}</td>
            <td>{order['customer']}</td>
            <td>{order['product']}</td>
            <td style="text-align: right;">{amt}</td>
            <td>{order['created_at']}</td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Sales & Operations Report</title>
    <style>
        @page {{
            size: A4;
            margin: 20mm;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            color: #1e293b;
            margin: 0;
            padding: 0;
            font-size: 13px;
            line-height: 1.5;
        }}
        .header {{
            margin-bottom: 24px;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 12px;
        }}
        .header h1 {{
            margin: 0 0 6px 0;
            font-size: 24px;
            color: #0f172a;
        }}
        .timestamp {{
            color: #64748b;
            font-size: 12px;
            margin: 0;
        }}
        .cards-grid {{
            display: flex;
            gap: 16px;
            margin-bottom: 24px;
        }}
        .card {{
            flex: 1;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 16px;
        }}
        .card-label {{
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #64748b;
            margin-bottom: 4px;
            font-weight: 600;
        }}
        .card-value {{
            font-size: 22px;
            font-weight: 700;
            color: #2563eb;
        }}
        h2 {{
            font-size: 16px;
            margin-top: 24px;
            margin-bottom: 12px;
            color: #0f172a;
            page-break-after: avoid;
            break-after: avoid;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 24px;
        }}
        thead {{
            display: table-header-group;
        }}
        th {{
            background-color: #f1f5f9;
            color: #334155;
            font-weight: 600;
            text-align: left;
            padding: 8px 12px;
            border-bottom: 2px solid #cbd5e1;
            font-size: 12px;
        }}
        td {{
            padding: 8px 12px;
            border-bottom: 1px solid #e2e8f0;
            font-size: 12px;
        }}
        tr {{
            break-inside: avoid;
            page-break-inside: avoid;
        }}
        tr:nth-child(even) {{
            background-color: #f8fafc;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Sales & Operations Report</h1>
        <p class="timestamp">Generated on: {timestamp_str}</p>
    </div>

    <div class="cards-grid">
        <div class="card">
            <div class="card-label">Total Orders</div>
            <div class="card-value">{total_orders}</div>
        </div>
        <div class="card">
            <div class="card-label">Total Revenue</div>
            <div class="card-value">{total_revenue}</div>
        </div>
    </div>

    <h2>Top 5 Products by Revenue</h2>
    <table>
        <thead>
            <tr>
                <th>Product Name</th>
                <th style="text-align: right;">Total Sales</th>
                <th style="text-align: right;">Units Sold</th>
            </tr>
        </thead>
        <tbody>
            {top_products_rows}
        </tbody>
    </table>

    <h2>Daily Summary (Last 7 Days)</h2>
    <table>
        <thead>
            <tr>
                <th>Date</th>
                <th style="text-align: right;">Order Count</th>
                <th style="text-align: right;">Daily Revenue</th>
            </tr>
        </thead>
        <tbody>
            {daily_orders_rows}
        </tbody>
    </table>

    <h2>Detailed Orders (~200 items)</h2>
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Customer</th>
                <th>Product</th>
                <th style="text-align: right;">Amount</th>
                <th>Timestamp</th>
            </tr>
        </thead>
        <tbody>
            {raw_orders_rows}
        </tbody>
    </table>
</body>
</html>
"""
    return html


async def render_pdf(html_content: str, output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(html_content, wait_until="networkidle")
        await page.pdf(path=output_path, format="A4", print_background=True)
        await browser.close()


if __name__ == "__main__":
    data = get_report_data()
    html_content = generate_report_html(data)
    target_path = os.path.join("reports", "test.pdf")
    asyncio.run(render_pdf(html_content, target_path))
    print(f"PDF generated successfully at {target_path}")
    print(f"File size: {os.path.getsize(target_path)} bytes")
