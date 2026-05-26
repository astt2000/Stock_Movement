import json
import urllib.request
import os

# API Configurations provided by user
FINNHUB_KEY = "d2530epr01qns40ctr90d2530epr01qns40ctr9g"
TWELVEDATA_KEY = "ac51c8bd269246109f27d4dec51bcc28"

def load_tickers_from_file(filename, default_list):
    """Reads stock symbols dynamically from a specified file path"""
    if not os.path.exists(filename):
        print(f"⚠️ Warning: {filename} not found. Creating a default file asset.")
        with open(filename, "w") as f:
            f.write(";".join(default_list))
        return default_list
    
    with open(filename, "r") as f:
        content = f.read().strip()
    
    tickers = [symbol.strip().upper() for symbol in content.split(";") if symbol.strip()]
    print(f"📋 Loaded {len(tickers)} symbols from {filename}: {tickers}")
    return tickers

def fetch_ticker_data(symbol):
    """Queries Finnhub with an automatic fallback mechanism to TwelveData"""
    # Try Finnhub (Primary)
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_KEY}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get('c') and data.get('c') != 0:
                return {
                    "price": float(data['c']),
                    "change": float(data.get('dp', 0)),
                    "prev_close": float(data.get('pc', data['c'])),
                    "open": float(data.get('o', data['c']))
                }
    except Exception as e:
        print(f"   ⚠️ Finnhub failed for {symbol}: {e}. Trying TwelveData fallback...")
    
    # Try TwelveData (Fallback)
    try:
        url = f"https://api.twelvedata.com/quote?symbol={symbol}&apikey={TWELVEDATA_KEY}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode('utf-8'))
            if "price" in data:
                return {
                    "price": float(data['price']),
                    "change": float(data.get('percent_change', 0)),
                    "prev_close": float(data.get('previous_close', data['price'])),
                    "open": float(data.get('open', data['price']))
                }
    except Exception as fe:
        print(f"   ❌ Critical: Fallback failed for {symbol}: {fe}")
    
    return None

def process_market_pipeline():
    # Load separate portfolios 
    list1_tickers = load_tickers_from_file("Stock_List.txt", ["ALAB","BBAI","BMNR","BTBT","ENVX","IOT","KEEL","KULR","LIDR"])
    list2_tickers = load_tickers_from_file("Stock_List2.txt", ["LUCD","LUNR","MVST","OKLO","QS","RKLB","RUM","SMR","SOFI","SOUN"])
    
    # Combine lists uniquely to save API calls
    all_unique_tickers = list(set(list1_tickers + list2_tickers))
    global_registry = {}

    for symbol in all_unique_tickers:
        print(f"🔄 Intercepting matrix data metrics for: {symbol}...")
        metrics = fetch_ticker_data(symbol)
        
        if metrics:
            price = metrics["price"]
            change = metrics["change"]
            simulated_rsi = max(15, min(85, 50 + (change * 2.5)))
            
            macd_str = "Neutral Phase"
            if change > 0.5:
                macd_str = "Bullish Crossover"
            elif change < -0.5:
                macd_str = "Bearish Realignment"

            global_registry[symbol] = {
                "sym": symbol,
                "price": price,
                "change": change,
                "rsi": simulated_rsi,
                "macdStr": macd_str,
                "history": [metrics["prev_close"], metrics["open"], price * 0.99, price * 1.01, price]
            }

    # Package the payload cleanly split by lists
    output_data = {
        "list1_symbols": list1_tickers,
        "list2_symbols": list2_tickers,
        "registry": global_registry
    }

    with open("./live_market.json", "w") as f:
        json.dump(output_data, f, indent=2)
    print("✨ Job complete. 'live_market.json' updated with list toggles.")

if __name__ == "__main__":
    process_market_pipeline()
