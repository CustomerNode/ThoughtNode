import requests
import yfinance

ticker = 'AAPL'

api_keys = {
    'financialmodelingprep':'ejlf7vrTU5El0Dd2qCoC3fg1ruw4PIwN',
    'alphavantage':'E4FRD722JXL04GXA',
    'polygon':'xoqwFzu0D8eyxuhtHikJBLKF2W16rbkM',
}

def getFinancialData(url):
    response = requests.get(url)
    results = response.json()
    print(results)
    print()

getFinancialData(f"https://financialmodelingprep.com/api/v3/quote/{ticker}?apikey={api_keys['financialmodelingprep']}")
getFinancialData(f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={ticker}&interval=5min&apikey={api_keys['alphavantage']}")
getFinancialData(f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/2024-01-01/2024-01-10?adjusted=true&sort=asc&limit=10&apiKey={api_keys['polygon']}")

ticker_data = yfinance.Ticker(ticker)
ticker_history = ticker_data.history(period="3mo")
print(ticker_history)