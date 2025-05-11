import requests
import yfinance as yf
from datetime import datetime
import time
import os

# Telegram Bot settings
TELEGRAM_TOKEN = "8198415223:AAEJkuvp-LuHL_1oU07AplEIMb3LnjxjuWw"  # <-- Replace with your token
CHAT_ID = "8198415223"  # <-- Replace with your chat_id


# Settings
ticker = "AAPL"
interval = 3600  # Run every 1 hour

# Define the function to send signals
def send_signal(action, price):
    message = f"📈 Stock Alert:\nTicker: {ticker}\nAction: {action}\nPrice: {price}\nTimestamp: {datetime.now().isoformat()}"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    params = {
        "chat_id": CHAT_ID,
        "text": message
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        print("✅ Message sent to Telegram!")
    else:
        print(f"⚠️ Failed to send message: {response.status_code}")

# Main loop for automation
while True:
    print(f"📈 Fetching latest data for {ticker}...")
    stock_data = yf.download(ticker, period='2d', interval='1h')
    stock_data.reset_index(inplace=True)

    # Feature Engineering
    stock_data['SMA_20'] = stock_data['Close'].rolling(window=20).mean()
    stock_data['SMA_50'] = stock_data['Close'].rolling(window=50).mean()
    stock_data['Signal'] = stock_data['SMA_20'] > stock_data['SMA_50']

    # Get the latest entry
    latest_data = stock_data.iloc[-1]
    price = float(latest_data['Close'])
    action = "BUY" if latest_data['Signal'].item() else "SELL"

    # Send signal
    print(f"🚀 Sending signal: {action} at {price}")
    send_signal(action, price)

    # Wait for the next run
    print(f"⏳ Waiting for {interval // 60} minutes before the next check...")
    time.sleep(interval)
