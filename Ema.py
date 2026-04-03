import requests
import pandas as pd
import time
import traceback
import telegram

# ============================
# TELEGRAM BOT
# ============================
TELEGRAM_TOKEN = "8174309758:AAFSEJ-QvTm0Yof1S6wi8fKStQehsIluZoU"
CHAT_ID = "8740478872"
bot = telegram.Bot(token=TELEGRAM_TOKEN)

# ============================
# BEZPEČNÉ REQUESTS → JSON WRAPPER
# ============================

def safe_json(resp, context=""):
    """Bezpečne dekóduje JSON, inak vráti None."""
    try:
        return resp.json()
    except Exception:
        print(f"❌ JSON ERROR ({context}):", resp.text[:200])
        return None

# ============================
# BYBIT API
# ============================

def get_bybit_symbols():
    url = "https://api.bybit.com/v5/market/instruments-info"
    params = {"category": "linear"}

    resp = requests.get(url, params=params)
    r = safe_json(resp, "symbols")

    if not r or r.get("retCode") != 0:
        print("Bybit symbol error:", r)
        return []

    return [x["symbol"] for x in r["result"]["list"]]


def get_bybit_klines(symbol, interval="60", limit=200):
    url = "https://api.bybit.com/v5/market/kline"
    params = {
        "category": "linear",
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }

    resp = requests.get(url, params=params)
    r = safe_json(resp, f"kline {symbol}")

    if not r or r.get("retCode") != 0:
        print("Bybit kline error:", symbol, r)
        return None

    rows = r["result"]["list"]

    df = pd.DataFrame(rows, columns=[
        "timestamp", "open", "high", "low", "close", "volume", "turnover"
    ])

    df["open"] = df["open"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["close"] = df["close"].astype(float)

    df = df.sort_values("timestamp")
    return df

# ============================
# EMA FUNKCIE
# ============================

def ema(df, period):
    return df["close"].ewm(span=period, adjust=False).mean()


def is_bullish_cross(df):
    df["ema13"] = ema(df, 13)
    df["ema50"] = ema(df, 50)

    last = df.iloc[-1]
    prev = df.iloc[-2]

    return prev["ema13"] < prev["ema50"] and last["ema13"] > last["ema50"]

# ============================
# HLAVNÁ SLUČKA
# ============================

sent = set()  # ochrana proti duplicitám

def main():
    bot.send_message(chat_id=CHAT_ID, text="🔍 Bybit EMA screener beží…")

    while True:
        try:
            symbols = get_bybit_symbols()

            for symbol in symbols:
                df = get_bybit_klines(symbol)
                if df is None:
                    continue

                if is_bullish_cross(df):
                    candle_id = f"{symbol}-{df.iloc[-1]['timestamp']}"

                    if candle_id not in sent:
                        sent.add(candle_id)

                        msg = f"📈 BULLISH CROSS: {symbol}"
                        print(msg)
                        bot.send_message(chat_id=CHAT_ID, text=msg)

            time.sleep(5)

        except Exception as e:
            print("ERROR:", e)
            traceback.print_exc()
            time.sleep(5)


if __name__ == "__main__":
    main()
