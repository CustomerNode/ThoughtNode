from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import requests
import os

firefox_options = Options()
firefox_options.add_argument("-headless")
driver = webdriver.Firefox(options=firefox_options)

ws_apis = {
    'google':{
        'API_KEY': 'AIzaSyCgHkxczahs-G5ApRyIz0Q9NSdSGxExtL8',
        'CSE_ID': 'c3625a090b42a40bb',
    },
}

def google_web_search(query,api_key,cse_id,num_results=3):
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
    link = None
    for item in results.get("items", []):
        print(f"Title: {item['title']}")
        print(f"Link: {item['link']}")
        link = item['link']
        driver.get(link)
        WebDriverWait(driver,20).until(EC.presence_of_all_elements_located((By.TAG_NAME, "body")))
        WebDriverWait(driver, 30).until(lambda d: d.execute_script('return document.readyState') == 'complete')
        contents = driver.find_element(By.TAG_NAME, "body")
        print(f"Contents: {contents.text}")

        links = driver.find_elements(By.TAG_NAME, "a")
        for linkedpage in links:
            if(driver.get(linkedpage.get_attribute("href"))):
                WebDriverWait(driver,20).until(EC.presence_of_all_elements_located((By.TAG_NAME, "body")))
                WebDriverWait(driver, 30).until(lambda d: d.execute_script('return document.readyState') == 'complete')
                contents = driver.find_element(By.TAG_NAME, "body")
                print(f"{link} Contents: {contents.text}")
        print("\n\n\n")
    driver.quit()

google_web_search('Apple Financial Forecast',ws_apis['google']['API_KEY'],ws_apis['google']['CSE_ID'])