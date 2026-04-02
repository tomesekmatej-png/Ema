import requests
import time
import json
import os

BASE_URL = "https://fapi.binance.com"

TOKEN = "8174309758:AAFSEJ-QvTm0Yof1S6wi8fKStQehsIluZoU"
CHAT_ID = 2682711
TELEGRAM_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

LOG_FILE = "screener_log.txt"
SIGNALS_FILE = "sent_signals.json"


def log(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {msg}\n")


def send_msg(text):
    try:
        requests.post(TELEGRAM_URL, data={"chat_id": CHAT_ID, "text": text})
        log(f"Sent: {text}")
    except Exception as e:
        log(f"Telegram error: {e}")


def public_get(endpoint, params=None):
    url = f"{BASE_URL}{endpoint}"
    try:
        r = requests.get(url, params=params, timeout=5)
        return r.json()
    except Exception as e:
        log(f"Request error: {e}")
        return None


def ema(values, period):
    k = 2 / (period + 1)
    ema_val = values[0]
    for price in values[1:]:
        ema_val = price * k + ema_val * (1 - k)
    return ema_val


def load_sent_signals():
    if not os.path.exists(SIGNALS_FILE):
        return {}
    with open(SIGNALS_FILE, "r") as f:
        return json.load(f)


def save_sent_signals(data):
    with open(SIGNALS_FILE, "w") as f:
        json.dump(data, f)


def get_usdt_pairs():
    data = public_get("/fapi/v1/exchangeInfo")

    if not data or "symbols" not in data:
        log(f"API ERROR: {data}")
        return []

    return [s["symbol"] for s in data["symbols"] if s["symbol"].endswith("USDT")]


def get_klines(symbol):
    params = {"symbol": symbol, "interval": "1h", "limit": 60}
    return public_get("/fapi/v1/klines", params)


def check_cross(symbol):
    kl = get_klines(symbol)

    if not isinstance(kl, list):
        log(f"Klines error for {symbol}: {kl}")
        return False

    closes = [float(c[4]) for c in kl]

    ema13_prev = ema(closes[:-1], 13)
    ema50_prev = ema(closes[:-1], 50)

    ema13_now = ema(closes, 13)
    ema50_now = ema(closes, 50)

    return ema13_prev < ema50_prev and ema13_now > ema50_now


def main():
    log("Starting EMA screener...")
    send_msg("🔍 EMA screener beží… kontrolujem 1h bullish crossy.")

    sent = load_sent_signals()
    pairs = get_usdt_pairs()

    if not pairs:
        send_msg("⚠️ Binance API error — žiadne páry.")
        return

    for symbol in pairs:
        try:
            if check_cross(symbol):
                if symbol not in sent:
                    send_msg(f"🚀 Bullish EMA 13/50 crossover na 1h: {symbol}")
                    sent[symbol] = True
                else:
                    log(f"Duplicate ignored: {symbol}")
        except Exception as e:
            log(f"{symbol} error: {e}")

    save_sent_signals(sent)
    log("Scan complete.")


if __name__ == "__main__":
    main()
