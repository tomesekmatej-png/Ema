import os
import time
import requests
import pandas as pd
from datetime import datetime, timedelta
from collections import deque
from binance.client import Client
from ta.trend import EMAIndicator

# Your webhook (as requested)
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1462512651719540909/54lVZyq06El1gUbDQDxocbawJE5xyy6aZRMviFfdD8dvuYzJH1bEZP7R0qq2JLN4CNTY"

# API keys optional
API_KEY = os.getenv("BINANCE_API_KEY", "")
API_SECRET = os.getenv("BINANCE_API_SECRET", "")

client = Client(API_KEY, API_SECRET)
memory = {}

def send_discord_alert(symbol, timestamp):
    message = {
        "content": (
            f"📈 **Bullish EMA 13 → EMA 50 Cross**\n"
            f"**Pair:** {symbol}\n"
            f"**Time:** {timestamp} UTC\n"
            f"**Timeframe:** 1H"
        )
    }
    requests.post(DISCORD_WEBHOOK, json=message)

def get_usdt_futures_symbols():
    info = client.futures_exchange_info()
    return [
        s["symbol"]
        for s in info["symbols"]
        if s["contractType"] == "PERPETUAL" and s["quoteAsset"] == "USDT"
    ]

def get_1h_klines(symbol, limit=200):
    return client.futures_klines(symbol=symbol, interval="1h", limit=limit)

def check_crosses(df):
    df["ema13"] = EMAIndicator(df["close"], window=13).ema_indicator()
    df["ema50"] = EMAIndicator(df["close"], window=50).ema_indicator()

    crosses = []
    for i in range(1, 6):
        prev = df.iloc[-(i+1)]
        last = df.iloc[-i]
        if prev["ema13"] < prev["ema50"] and last["ema13"] > last["ema50"]:
            crosses.append(last["time"])
    return crosses

def run_scanner():
    print("🚀 Loading USDT-M futures symbols...")
    symbols = get_usdt_futures_symbols()

    for s in symbols:
        memory[s] = deque(maxlen=20)

    print(f"Tracking {len(symbols)} pairs")
    print("Checking last 5 closed candles...\n")

    # Initial scan
    for symbol in symbols:
        try:
            klines = get_1h_klines(symbol)
            df = pd.DataFrame(klines, columns=[
                "time","open","high","low","close","volume",
                "close_time","quote_asset_volume","trades",
                "taker_buy_base","taker_buy_quote","ignore"
            ])
            df["close"] = df["close"].astype(float)
            df["time"] = pd.to_datetime(df["time"], unit="ms")

            crosses = check_crosses(df)
            for ts in crosses:
                if ts not in memory[symbol]:
                    memory[symbol].append(ts)
                    send_discord_alert(symbol, ts)

        except Exception:
            pass

    print("Initial scan done. Waiting for next hourly candle...\n")

    # Hourly loop
    while True:
        now = datetime.utcnow()
        next_hour = (now + timedelta(hours=1)).replace(minute=0, second=5, microsecond=0)
        time.sleep((next_hour - now).total_seconds())

        print(f"Checking new 1H candle at {datetime.utcnow()} UTC")

        for symbol in symbols:
            try:
                klines = get_1h_klines(symbol)
                df = pd.DataFrame(klines, columns=[
                    "time","open","high","low","close","volume",
                    "close_time","quote_asset_volume","trades",
                    "taker_buy_base","taker_buy_quote","ignore"
                ])
                df["close"] = df["close"].astype(float)
                df["time"] = pd.to_datetime(df["time"], unit="ms")

                crosses = check_crosses(df)
                for ts in crosses:
                    if ts not in memory[symbol]:
                        memory[symbol].append(ts)
                        send_discord_alert(symbol, ts)

            except Exception:
                pass

if __name__ == "__main__":
    run_scanner()
