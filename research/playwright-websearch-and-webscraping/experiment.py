from playwright.async_api import async_playwright
from urllib.robotparser import RobotFileParser
from urllib.request import Request,urlopen
from urllib.parse import urlparse
from PyPDF2 import PdfReader
from io import BytesIO
import requests
import asyncio
import aiohttp
import time
import os

ws_apis = {
    'google':{
        'API_KEY':'AIzaSyCgHkxczahs-G5ApRyIz0Q9NSdSGxExtL8',
        'CSE_ID':'c3625a090b42a40bb',
    },
}

async def readPDF(session,link):
    try:
        async with session.get(link) as response:
            content = await response.read()
            pdf = PdfReader(BytesIO(content))
            os.makedirs("scraped",exist_ok=True)
            filename = f"untitled-{time.time()}" if pdf.metadata.title == '' else pdf.metadata.title
            with open(f"scraped/{filename}","w") as file:
                for i in range(len(pdf.pages)):
                    file.write(pdf.pages[i].extract_text())
    except Exception as e:
        raise Exception(f"read pdf fail: {link}: {e}")

async def playwright_webscrape(browser,link):
    pdf_links,img_links,links = [],[],[]
    page = await browser.new_page()
    try:
        await page.goto(link,timeout=10000)
        await page.wait_for_load_state()
        await page.wait_for_load_state("domcontentloaded")
        os.makedirs("scraped",exist_ok=True)
        title = await page.title()
        filename = f"untitled-{time.time()}" if title == '' else title
        with open(f"scraped/{filename}","w") as file:
            file.write(await page.inner_text("body"))

        pdf_links = await page.eval_on_selector_all(
            'a[href$=".pdf"]', "elements => elements.map(e => e.href)"
        )
        img_links = await page.eval_on_selector_all(
            "img[src]", "elements => elements.map(e => e.src)"
        )
        links = await page.eval_on_selector_all(
            'a[href]', "elements => elements.map(e => e.href)"
        )

        # ensure above scraping sufficiently captures page data from variety of sources

        await page.screenshot(path=f"scraped/untitledscreenshot-{time.time()}.png" if title == '' else f"scraped/screenshot-{title}.png",full_page=True)

        await page.close()
        return pdf_links,img_links,links
    except Exception as e:
        await page.close()
        raise Exception(f"webscrape fail: {link}: {e}")

async def webscrape_allowed(session,link):
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'}
    robots_url = urlparse(link).scheme+"://"+urlparse(link).netloc+"/robots.txt"
    rp = RobotFileParser()
    try:
        async with session.get(robots_url,headers=headers,timeout=10) as response:
            if response.status != 200:
                raise Exception(f"{response.status} {response.reason}")
            content = await response.text()
            rp.parse(content.splitlines())
            return rp.can_fetch("*",link)
    except Exception as e:
        raise Exception(f"robots.txt open fail: {link}: {repr(e)}")

def google_web_search(query,api_key,cse_id,num_results=10):
    url = 'https://www.googleapis.com/customsearch/v1'
    params = {
        "q": query,
        "key": api_key,
        "cx": cse_id,
        "num": num_results
    }
    try:
        response = requests.get(url=url,params=params)
        response.raise_for_status()
        results = response.json()
    except Exception as e:
        raise Exception(f"google web search fail: {params}: {e}")
    return [item["link"] for item in results.get("items",[])]

async def main(): # check robots, scrape, and crawl asynchronously
    links = google_web_search('Apple Financial Forecast',ws_apis['google']['API_KEY'],ws_apis['google']['CSE_ID'])
    async with async_playwright() as p:
        async with aiohttp.ClientSession() as session:
            browser = await p.firefox.launch(headless=True)
            allowed_tasks,scrape_tasks = {},{}

            for link in links:
                allowed_tasks[link] = webscrape_allowed(session,link)
            allowed_task_results = await asyncio.gather(*(list(allowed_tasks.values())),return_exceptions=True)

            for i,result in enumerate(allowed_task_results):
                if result == True:
                    if "pdf" in links[i].lower():
                        scrape_tasks[links[i]] = readPDF(session,links[i])
                    else:
                        scrape_tasks[links[i]] = playwright_webscrape(browser,links[i])
                else:
                    print(result)
            scrape_task_results = await asyncio.gather(*(list(scrape_tasks.values())),return_exceptions=True)

            for i,result in enumerate(scrape_task_results):
                if isinstance(result, Exception):
                    print(f"webscrape fail: {list(scrape_tasks.keys())[i]}: {result}")
                else:
                    print(f"webscrape success: {list(scrape_tasks.keys())[i]}")

            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())