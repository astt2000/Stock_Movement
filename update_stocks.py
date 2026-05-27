import json
import os
from datetime import datetime
import yfinance as yf
import pandas as pd

def load_tickers_from_file(filename, default_list):
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            f.write(";".join(default_list))
        return default_list
    with open(filename, "r") as f:
        content = f.read().strip()
    return [symbol.strip().upper() for symbol in content.split(";") if symbol.strip()]

def calculate_technical_indicators(df):
    """Calculates professional-grade mathematical RSI-14 and MACD parameters"""
    if len(df) < 30:
        return 50.0, "Neutral Phase", 0.0
    
    # 1. True RSI-14 Calculation
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    rsi = 100 - (100 / (1 + rs))
    current_rsi = float(rsi.iloc[-1])
    
    # 2. True MACD Calculation (12, 26, 9 parameter standard)
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    macd_histogram = macd_line - signal_line
    
    current_hist = macd_histogram.iloc[-1]
    prev_hist = macd_histogram.iloc[-2]
    
    # Dynamic Phase Realignment Logic
    if current_hist > 0 and prev_hist <= 0:
        macd_str = "Bullish Crossover"
    elif current_hist < 0 and prev_hist >= 0:
        macd_str = "Bearish Realignment"
    elif current_hist > 0:
        macd_str = "Bullish Momentum"
    else:
        macd_str = "Bearish Momentum"
        
    return current_rsi, macd_str, float(df['Close'].iloc[-1])

def process_market_pipeline():
    list1_tickers = load_tickers_from_file("Stock_List.txt", ["ALAB","BBAI","BMNR","BTBT","ENVX","IOT","KEEL","KULR","LIDR"])
    list2_tickers = load_tickers_from_file("Stock_List2.txt", ["LUCD","LUNR","MVST","OKLO","QS","RKLB","RUM","SMR","SOFI","SOUN","NVDA","AAPL"])
    
    all_unique_tickers = list(set(list1_tickers + list2_tickers))
    global_registry = {}
    
    # Download 60 days of historical data via batch to bypass API rate caps
    print(f"📡 Downloading institutional candle charts for {len(all_unique_tickers)} assets...")
    tickers_string = " ".join(all_unique_tickers)
    data = yf.download(tickers_string, period="60d", interval="1d", group_by='ticker', progress=False)
    
    for symbol in all_unique_tickers:
        try:
            # Handle both single-ticker and multi-ticker DataFrame shapes safely
            df = data[symbol] if len(all_unique_tickers) > 1 else data
            df = df.dropna(subset=['Close'])
            
            if df.empty or len(df) < 5:
                continue
                
            current_price = float(df['Close'].iloc[-1])
            prev_close = float(df['Close'].iloc[-2])
            pct_change = ((current_price - prev_close) / prev_close) * 100
            
            # Extract true mathematical signal properties
            true_rsi, true_macd_str, _ = calculate_technical_indicators(df)
            
            # Extract trailing historical close points for the sparkline chart array
            trailing_history = df['Close'].tail(5).tolist()
            
            global_registry[symbol] = {
                "sym": symbol,
                "price": current_price,
                "change": pct_change,
                "rsi": true_rsi,
                "macdStr": true_macd_str,
                "history": trailing_history
            }
            print(f"   ✅ Processed metrics for: {symbol} | RSI: {true_rsi:.1f} | {true_macd_str}")
        except Exception as e:
            print(f"   ⚠️ Skipping {symbol}: Technical computation boundary error ({e})")

    sync_time = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    output_data = {
        "sync_timestamp": sync_time,
        "list1_symbols": list1_tickers,
        "list2_symbols": list2_tickers,
        "registry": global_registry
    }
    
    with open("./live_market.json", "w") as f:
        json.dump(output_data, f, indent=2)
    print(f"✨ Job complete. 'live_market.json' database updated with true calculations at {sync_time}.")

if __name__ == "__main__":
    process_market_pipeline()