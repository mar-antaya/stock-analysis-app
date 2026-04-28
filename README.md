# Stock Analysis App

A lightweight Flask API that fetches daily stock prices from [Alpha Vantage](https://www.alphavantage.co/), stores them in SQLite, and computes rolling average daily returns.

Built by [@mar_antaya](https://github.com/mar-antaya) as part of an applied ML portfolio.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/stock?symbol=AAPL` | Look up stored price data by ticker symbol |
| `GET` | `/api/rolling-average?symbol=AAPL` | Fetch live prices and return rolling average daily returns (window=5) |

## Local Setup

```bash
# Clone and enter the project
git clone https://github.com/mar-antaya/stock-analysis-app.git
cd stock-analysis-app

# Create a virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and add your Alpha Vantage API key

# Run locally
source .env && python stock_analysis.py
```

The server starts on `http://localhost:5000` by default.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ALPHA_VANTAGE_API_KEY` | Yes | Your Alpha Vantage API key ([get one here](https://www.alphavantage.co/support/#api-key)) |
| `ALPHA_VANTAGE_API_SECRET` | No | API secret (if applicable) |
| `FLASK_DEBUG` | No | Set to `true` or `1` for debug mode (defaults to `false`) |
| `PORT` | No | Server port (defaults to `5000`; set automatically by Render/Railway) |

## Deploy to Render

1. Push this repo to GitHub.
2. Create a new **Web Service** on [Render](https://render.com).
3. Connect your GitHub repo and select the `main` branch.
4. Render auto-detects the `Procfile`. Set the following:
   - **Build command**: `pip install -r requirements.txt`
   - **Start command**: (leave blank — Procfile handles it)
5. Add `ALPHA_VANTAGE_API_KEY` in the **Environment** tab.
6. Deploy.

The app binds to `0.0.0.0` and reads `PORT` from the environment, which Render sets automatically.
