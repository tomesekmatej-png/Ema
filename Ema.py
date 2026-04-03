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

DEBUG = True  # zapni/vypni debug logy

# ============================
# BINANCE API
# ============================

def get_binance_symbols():
    if DEBUG:
        print("🔎 Načítavam symboly z Binance...")

    url = "https://api.binance.com/api/v3/exchangeInfo"
    resp = requests.get(url, timeout=10)

    try:
        data = resp.json()
    except:
        print("❌ JSON ERROR (symbols):", resp.text[:200])
        return []

    symbols = [
        s["symbol"]
        for s in data["symbols"]
        if s["status"] == "TRADING" and s["quoteAsset"] == "USDT"
    ]

    if DEBUG:
        print(f"✅ Symboly načítané: {len(symbols)} párov")

    return symbols


def get_binance_klines(symbol, interval="1h", limit=200):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}

    resp = requests.get(url, params=params, timeout=10)

    try:
        data = resp.json()
    except:
        print(f"❌ JSON ERROR (klines {symbol}):", resp.text[:200])
        return None

    if not isinstance(data, list):
        print(f"❌ Binance kline error: {symbol}", data)
        return None

    df = pd.DataFrame(data, columns=[
        "timestamp", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "trades", "taker_base",
        "taker_quote", "ignore"
    ])

    df["open"] = df["open"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["close"] = df["close"].astype(float)

    if DEBUG:
        print(f"📊 {symbol}: {len(df)} sviečok načítaných")

    return df

# ============================
# EMA FUNKCIE
# ============================

def ema(df, period):
    return df["close"].ewm(span=period, adjust=False).mean()


def is_bullish_cross(df, symbol):
    df["ema13"] = ema(df, 13)
    df["ema50"] = ema(df, 50)

    last = df.iloc[-1]
    prev = df.iloc[-2]

    if DEBUG:
        print(f"📈 EMA {symbol}: 13={last['ema13']:.4f} | 50={last['ema50']:.4f}")

    return prev["ema13"] < prev["ema50"] and last["ema13"] > last["ema50"]

# ============================
# HLAVNÁ SLUČKA
# ============================

sent = set()

def main():
    bot.send_message(chat_id=CHAT_ID, text="🔍 Binance EMA screener beží…")

    while True:
        try:
            symbols = get_binance_symbols()

            for symbol in symbols:
                df = get_binance_klines(symbol)
                if df is None:
                    continue

                if is_bullish_cross(df, symbol):
                    candle_id = f"{symbol}-{df.iloc[-1]['timestamp']}"

                    if candle_id not in sent:
                        sent.add(candle_id)

                        msg = f"📈 BULLISH CROSS: {symbol}"
                        print(msg)
                        bot.send_message(chat_id=CHAT_ID, text=msg)

            time.sleep(5)

        except Exception as e:
            print("❌ ERROR:", e)
            traceback.print_exc()
            time.sleep(5)


if __name__ == "__main__":
    main()
