import yfinance as yf
import pandas as pd
import requests
import time
from datetime import datetime

# === Telegram Bot Settings ===
TELEGRAM_TOKEN = "8198415223:AAEJkuvp-LuHL_1oU07AplEIMb3LnjxjuWw"
CHAT_ID = "126902456"

# === Indicator Toggles ===
USE_RSI = True
USE_EMA = True
USE_MACD = True
USE_BOLLINGER = True
USE_VOLUME = True

# === Indicator Parameters ===
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

EMA_FAST = 12
EMA_SLOW = 26

MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

BB_PERIOD = 20
BB_STD_DEV = 2

VOLUME_LOOKBACK = 20

# === Timeframes to Analyze ===
TIMEFRAMES = [
    {"label": "Short", "period": "10d", "interval": "1h"},
    {"label": "Medium", "period": "1mo", "interval": "4h"},
    {"label": "Long", "period": "3mo", "interval": "1d"},
]

# === Tickers to Track ===
TICKERS = ["AMZN", "NVDA", "AMD", "GOOG", "META", "BITF", "QBTS", "TSLA", "BYDDF", "INVZ", "ALGS", "HOOD", "RVPH", "MBLY"]

# === Telegram Alert Sender ===
def send_signal(ticker, action, price):
    message = f"📈 Signal: {action}\nTicker: {ticker}\nPrice: ${price:.2f}\nTime: {datetime.now().isoformat()}"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": message}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        print("✅ Message sent to Telegram!")
    else:
        print(f"❌ Telegram error: {response.text}")

# === Indicator Calculations ===
def calculate_indicators(df):
    if USE_RSI:
        delta = df['Close'].diff()
        gain = delta.clip(lower=0).rolling(RSI_PERIOD).mean()
        loss = -delta.clip(upper=0).rolling(RSI_PERIOD).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

    if USE_EMA:
        df['EMA_FAST'] = df['Close'].ewm(span=EMA_FAST, adjust=False).mean()
        df['EMA_SLOW'] = df['Close'].ewm(span=EMA_SLOW, adjust=False).mean()

    if USE_MACD:
        ema_fast = df['Close'].ewm(span=MACD_FAST, adjust=False).mean()
        ema_slow = df['Close'].ewm(span=MACD_SLOW, adjust=False).mean()
        df['MACD'] = ema_fast - ema_slow
        df['MACD_SIGNAL'] = df['MACD'].ewm(span=MACD_SIGNAL, adjust=False).mean()

    if USE_BOLLINGER:
        df['BB_MID'] = df['Close'].rolling(BB_PERIOD).mean()
        df['BB_STD'] = df['Close'].rolling(BB_PERIOD).std()
        df['BB_UPPER'] = df['BB_MID'] + BB_STD_DEV * df['BB_STD']
        df['BB_LOWER'] = df['BB_MID'] - BB_STD_DEV * df['BB_STD']

    if USE_VOLUME:
        df['VOL_AVG'] = df['Volume'].rolling(VOLUME_LOOKBACK).mean()

    return df

# === Signal Decision Logic ===
def generate_signal(df):
    if df.empty or len(df) < 50:
        print("⚠️ Not enough data.")
        return "HOLD"

    signals = []

    if USE_RSI:
        rsi = df['RSI'].iloc[-1]
        if rsi < RSI_OVERSOLD:
            signals.append("BUY")
        elif rsi > RSI_OVERBOUGHT:
            signals.append("SELL")

    if USE_EMA:
        ema_fast = df['EMA_FAST'].iloc[-1]
        ema_slow = df['EMA_SLOW'].iloc[-1]
        if ema_fast > ema_slow:
            signals.append("BUY")
        else:
            signals.append("SELL")

    if USE_MACD:
        macd = df['MACD'].iloc[-1]
        macd_signal = df['MACD_SIGNAL'].iloc[-1]
        if macd > macd_signal:
            signals.append("BUY")
        else:
            signals.append("SELL")

    if USE_BOLLINGER:
        close = df['Close'].iloc[-1].item() if hasattr(df['Close'].iloc[-1], 'item') else df['Close'].iloc[-1]
        bb_upper = df['BB_UPPER'].iloc[-1].item() if hasattr(df['BB_UPPER'].iloc[-1], 'item') else df['BB_UPPER'].iloc[-1]
        bb_lower = df['BB_LOWER'].iloc[-1].item() if hasattr(df['BB_LOWER'].iloc[-1], 'item') else df['BB_LOWER'].iloc[-1]
        if close < bb_lower:
            signals.append("BUY")
        elif close > bb_upper:
            signals.append("SELL")

    if USE_VOLUME:
        vol = df['Volume'].iloc[-1].item() if hasattr(df['Volume'].iloc[-1], 'item') else df['Volume'].iloc[-1]
        vol_avg = df['VOL_AVG'].iloc[-1].item() if hasattr(df['VOL_AVG'].iloc[-1], 'item') else df['VOL_AVG'].iloc[-1]
        if vol > vol_avg:
            signals.append("BUY")

    if not signals:
        return "HOLD"

    return "BUY" if signals.count("BUY") > signals.count("SELL") else "SELL"


# === Main Execution Loop ===
while True:
    for ticker in TICKERS:
        actions = []
        for tf in TIMEFRAMES:
            print(f"🔍 {tf['label']} timeframe for {ticker}...")
            df = yf.download(ticker, period=tf["period"], interval=tf["interval"])
            df = calculate_indicators(df).dropna()
            action = generate_signal(df)
            print(f"🧠 {tf['label']} signal: {action}")
            actions.append(action)

        # Final decision across timeframes
        if actions.count("BUY") > actions.count("SELL"):
            final_decision = "BUY"
        elif actions.count("SELL") > actions.count("BUY"):
            final_decision = "SELL"
        else:
            final_decision = "HOLD"

        if final_decision != "HOLD":
            latest_price = float(df['Close'].iloc[-1])
            send_signal(ticker, final_decision, latest_price)
        else:
            print("🤔 Final decision: HOLD")

    print("⏳ Waiting 1 hour before next check...\n")
    time.sleep(3600)
