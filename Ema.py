import requests
import pandas as pd
import numpy as np
import time
import telegram

# ====== TVOJE ÚDAJE ======
TOKEN = "7168409918:AAH5d0y1q8oJq8h0YzZ4t2Yv5uYqv6p6x0A"
CHAT_ID = "6915309850"
# =========================

bot = telegram.Bot(token=TOKEN)

def get_symbols():
    url = "https://api.binance.com/api/v3/exchangeInfo"
    data = requests.get(url, timeout=10).json()
    return [
        s["symbol"]
        for s in data["symbols"]
        if s["quoteAsset"] == "USDT" and s["status"] == "TRADING"
    ]

def get_klines(symbol):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": "1h", "limit": 200}
    data = requests.get(url, params=params, timeout=10).json()

    df = pd.DataFrame(data, columns=[
        "time","open","high","low","close","vol",
        "ct","qv","tr","tb","tq","i"
    ])

    df["close"] = df["close"].astype(float)
    return df

def ema_cross(df):
    df["ema13"] = df["close"].ewm(span=13, adjust=False).mean()
    df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()

    prev = df.iloc[-2]
    last = df.iloc[-1]

    return prev["ema13"] < prev["ema50"] and last["ema13"] > last["ema50"]

sent = set()

def main():
    bot.send_message(chat_id=CHAT_ID, text="🚀 EMA bot spustený (pandas 2.x, Binance API)")

    while True:
        try:
            symbols = get_symbols()

            for s in symbols:
                df = get_klines(s)
                if df is None or len(df) < 60:
                    continue

                if ema_cross(df):
                    cid = f"{s}-{df.iloc[-1]['time']}"
                    if cid not in sent:
                        sent.add(cid)
                        bot.send_message(chat_id=CHAT_ID, text=f"📈 EMA CROSS: {s}")

            time.sleep(5)

        except Exception as e:
            print("ERROR:", e)
            time.sleep(5)

if __name__ == "__main__":
    main()
