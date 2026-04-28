import os
import sqlite3
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ============================================================
# Stock Analysis App — Fetches market data & serves an API
# ============================================================

# Alpha Vantage API credentials (read from environment)
API_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY", "")
API_SECRET = os.environ.get("ALPHA_VANTAGE_API_SECRET", "")
if not API_KEY:
    raise RuntimeError("ALPHA_VANTAGE_API_KEY environment variable is required")

DATABASE = "stocks.db"


def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            date TEXT NOT NULL,
            close_price REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def fetch_stock_data(symbol):
    """Fetch daily stock prices from Alpha Vantage."""
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "apikey": API_KEY,
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    if "Error Message" in data:
        raise ValueError(f"Alpha Vantage error: {data['Error Message']}")
    if "Note" in data:
        raise ValueError(f"Alpha Vantage rate limit: {data['Note']}")
    if "Time Series (Daily)" not in data:
        raise ValueError(f"Unexpected Alpha Vantage response: {list(data.keys())}")

    time_series = data["Time Series (Daily)"]
    prices = []
    for date, values in time_series.items():
        prices.append({
            "date": date,
            "close": float(values["4. close"]),
        })
    return prices


def store_prices(symbol, prices):
    """Save fetched prices into the database."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    for p in prices:
        cursor.execute(
            "INSERT INTO stocks (symbol, date, close_price) VALUES (?, ?, ?)",
            (symbol, p["date"], p["close"]),
        )
    conn.commit()
    conn.close()


def compute_rolling_average_return(prices, window=5):
    """Calculate the rolling average return over a given window.

    Expects a list of dicts with 'date' and 'close' keys.
    Sorts by date ascending before computing returns.
    """
    # Convert closing prices to daily percent change first
    sorted_prices = sorted(prices, key=lambda p: p["date"])
    closes = [p["close"] for p in sorted_prices]
    daily_returns = []
    for i in range(1, len(closes)):
        pct_change = ((closes[i] - closes[i - 1]) / closes[i - 1]) * 100
        daily_returns.append(pct_change)

    # Compute rolling average of the daily returns
    rolling_averages = []
    for i in range(len(daily_returns) - window + 1):
        window_slice = daily_returns[i : i + window]
        avg = sum(window_slice) / len(window_slice)
        rolling_averages.append(round(avg, 4))

    return rolling_averages


# ----- Flask API Routes -----

@app.route("/api/stock", methods=["GET"])
def get_stock():
    """Look up stored stock data by symbol."""
    symbol = request.args.get("symbol")
    if not symbol:
        return jsonify({"error": "symbol query parameter is required"}), 400

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, symbol, date, close_price FROM stocks WHERE symbol = ?",
        (symbol,),
    )
    rows = cursor.fetchall()
    conn.close()

    results = [
        {"id": r[0], "symbol": r[1], "date": r[2], "close_price": r[3]}
        for r in rows
    ]
    return jsonify(results)


@app.route("/api/rolling-average", methods=["GET"])
def rolling_average():
    """Return the rolling average return for a stock."""
    symbol = request.args.get("symbol", "AAPL")
    try:
        prices = fetch_stock_data(symbol)
    except (requests.RequestException, ValueError) as e:
        return jsonify({"error": str(e)}), 502

    if not prices:
        return jsonify({"error": "No data found"}), 404

    store_prices(symbol, prices)
    averages = compute_rolling_average_return(prices)
    return jsonify({"symbol": symbol, "rolling_averages": averages})


if __name__ == "__main__":
    init_db()
    debug = os.environ.get("FLASK_DEBUG", "false").lower() in ("1", "true")
    port = int(os.environ.get("PORT", 5000))
    print("Starting Stock Analysis server ...")
    app.run(debug=debug, host="0.0.0.0", port=port)
