import requests

ws_apis = {
    'google':{
        'API_KEY': 'AIzaSyCgHkxczahs-G5ApRyIz0Q9NSdSGxExtL8',
        'CSE_ID': 'c3625a090b42a40bb',
    },
}

def google_search(query,api_key,cse_id,num_results=3):
    url = 'https://www.googleapis.com/customsearch/v1'
    params = {
        "q": query,
        "key": api_key,
        "cx": cse_id,
        "num": num_results
    }
    response = requests.get(url,params=params)
    response.raise_for_status()
    results = response.json()
    for item in results.get("items", []):
        print(item['title'])
        print(item['link'])
        print(item['snippet'])
        print()

google_search('Apple Financial Forecast',ws_apis['google']['API_KEY'],ws_apis['google']['CSE_ID'])