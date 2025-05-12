import requests
import yfinance as yf
from datetime import datetime
import time

# Telegram Bot settings
TELEGRAM_TOKEN = "8198415223:AAEJkuvp-LuHL_1oU07AplEIMb3LnjxjuWw"
CHAT_ID = "126902456"

# Settings
tickers = [ "AMZN", "NVDA" , "AMD", "GOOG", "META", "BITF", "QBTS", "TSLA", "BYDDF", "INVZ", "ALGS", "HOOD", "RVPH", "MBLY"]
interval = 1800  # Run every 30 minutes

# Define the function to send signal
def send_signal(ticker, action, price, timeframe):
    message = f"📈 Stock Alert:\nTicker: {ticker}\nAction: {action}\nTimeframe: {timeframe}\nPrice: {price}\nTimestamp: {datetime.now().isoformat()}"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    params = {
        "chat_id": CHAT_ID,
        "text": message
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        print(f"✅ Message sent to Telegram for {timeframe} - {ticker}!")
    else:
        print(f"⚠️ Failed to send message for {timeframe} - {ticker}: {response.status_code}")
        print(response.text)

# Function to fetch and analyze data
def analyze_data(ticker, period, interval, timeframe):
    print(f"📈 Fetching latest data for {ticker} - {timeframe}...")
    stock_data = yf.download(ticker, period=period, interval=interval)
    stock_data.reset_index(inplace=True)

    # Feature Engineering
    stock_data['SMA_20'] = stock_data['Close'].rolling(window=20).mean()
    stock_data['SMA_50'] = stock_data['Close'].rolling(window=50).mean()
    stock_data['Signal'] = stock_data['SMA_20'] > stock_data['SMA_50']

    # Get the latest entry
    latest_data = stock_data.iloc[-1]
    price = float(latest_data['Close'])
    action = "BUY" if latest_data['Signal'].item() else "SELL"

    print(f"🚀 {timeframe} signal for {ticker}: {action} at {price}")
    return action, price

# Main loop for automation
while True:
    for ticker in tickers:
        print(f"🔎 Analyzing {ticker}...")

        # Analyze different timeframes
        action_10d, price_10d = analyze_data(ticker, '10d', '1h', 'Short-term')
        action_1mo, price_1mo = analyze_data(ticker, '1mo', '4h', 'Medium-term')
        action_3mo, price_3mo = analyze_data(ticker, '3mo', '1d', 'Long-term')

        # Final Decision Logic
        actions = [action_10d, action_1mo, action_3mo]
        if actions.count("BUY") >= 2:
            final_action = "STRONG BUY"
            send_signal(ticker, final_action, price_10d, "Multi-Timeframe")
        elif actions.count("SELL") >= 2:
            final_action = "STRONG SELL"
            send_signal(ticker, final_action, price_10d, "Multi-Timeframe")
        else:
            final_action = "HOLD"
            print(f"🤔 No strong signal for {ticker}, holding position...")

    # Wait for the next run
    print(f"⏳ Waiting for {interval // 60} minutes before the next check...")
    time.sleep(interval)
