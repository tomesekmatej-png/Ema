import requests
import time
import telebot

TOKEN = "7168409918:AAH5d0y1q8oJq8h0YzZ4t2Yv5uYqv6p6x0A"
CHAT_ID = "6915309850"

bot = telebot.TeleBot(TOKEN)

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
    closes = [float(c[4]) for c in data]
    return closes

def ema(values, period):
    k = 2 / (period + 1)
    ema_val = values[0]
    for price in values[1:]:
        ema_val = price * k + ema_val * (1 - k)
    return ema_val

def ema_cross(closes):
    ema13_prev = ema(closes[:-1], 13)
    ema50_prev = ema(closes[:-1], 50)

    ema13_now = ema(closes, 13)
    ema50_now = ema(closes, 50)

    return ema13_prev < ema50_prev and ema13_now > ema50_now

sent = set()

def main():
    bot.send_message(CHAT_ID, "🚀 EMA bot spustený (bez pandas, bez imghdr)")

    while True:
        try:
            symbols = get_symbols()

            for s in symbols:
                closes = get_klines(s)
                if len(closes) < 60:
                    continue

                if ema_cross(closes):
                    cid = f"{s}-{int(time.time())}"
                    if cid not in sent:
                        sent.add(cid)
                        bot.send_message(CHAT_ID, f"📈 EMA CROSS: {s}")

            time.sleep(5)

        except Exception as e:
            print("ERROR:", e)
            time.sleep(5)

if __name__ == "__main__":
    main()
