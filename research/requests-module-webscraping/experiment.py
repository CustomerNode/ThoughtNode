from bs4 import BeautifulSoup
import requests

def test(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text,'html.parser')
    print(soup.body.text)
    print(soup.title.text)

test('https://www.cnn.com/us/live-news/la-protests-ice-raids-trump-06-10-25')
test('https://www.wsj.com/tech/ai/google-ai-news-publishers-7e687141?mod=hp_lista_pos2')
test('https://www.cnbc.com/2025/06/04/apple-samsung-smartphone-growth-cut-due-to-tariffs-analysts.html')
test('https://www.reuters.com/business/media-telecom/idc-cuts-global-smartphone-shipments-forecast-tariff-volatility-2025-05-29/')
test('https://finance.yahoo.com/news/apple-aapl-downgraded-hold-needham-122455533.html')
test('https://www.nasdaq.com/articles/apple-stock-q4-forecast-can-iphone-16-take-aapl-record-highs')
test('https://www.bloomberg.com/news/videos/2025-05-01/investors-await-apple-s-forecast-video')
test('https://www.msn.com/en-us/money/topstocks/apple-stock-price-forecast-major-concerns-remain/ar-AA1AhImG')
test('https://www.morningstar.com/funds/how-attractive-is-private-equity')
test('https://seekingalpha.com/article/4793854-uncut-gems-5-stocks-set-to-shine-amid-us-china-trade-talks')
test('https://www.marketwatch.com/livecoverage/stock-market-today-dow-s-p-nasdaq-dip-as-trade-uncertainty-lingers-and-cpi-inflation-report-due?mod=home_lead')
test('https://www.ft.com/content/f5a904c2-1ba7-47b4-a506-b9db7e899704')
test('https://www.usatoday.com/story/money/2025/01/31/stocks-get-boost-as-apple-sales-rise/78083818007/')
test('https://www.forex.com/ie/news-and-analysis/dow-jones-forecast-djia-slump-as-trump-threatens-eu-apple-with-higher-tariffs-us-open-2025-5-23/')
test('https://www.barrons.com/livecoverage/apple-earnings-stock-price-news/card/apple-s-outlook-suggests-that-june-quarter-revenue-will-be-in-line-with-estimates-bFrcIIF6a6WhtcjssJou')
test('https://www.investors.com/research/magnificent-seven-stocks-june-2025/')
test('https://www.fxempire.com/forecasts/article/sp500-and-nasdaq-100-apple-powers-tech-rebound-stock-market-forecast-mixed-1511741')
test('https://www.investing.com/news/transcripts/earnings-call-transcript-apple-q1-2025-beats-eps-forecast-stock-falls-93CH-4018568')