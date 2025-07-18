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
        'API_KEY':os.getenv("GOOGLE_SEARCH_API_KEY"),
        'CSE_ID':os.getenv("GOOGLE_SEARCH_CSE_ID"),
    },
}

async def readPDF(session,link):
    try:
        async with session.get(link) as response:
            content = await response.read()
            pdf = PdfReader(BytesIO(content))
            os.makedirs("scraped",exist_ok=True)
            filename = f"untitled-{time.time()}" if pdf.metadata.title == '' else pdf.metadata.title
            valid_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ._-"
            filename = ''.join(char if char in valid_chars else '_' for char in filename)
            filename = filename[:255]
            with open(f"scraped/{filename}","w",encoding="utf-8") as file:
                for i in range(len(pdf.pages)):
                    file.write(pdf.pages[i].extract_text())
    except Exception as e:
        raise Exception(f"read pdf fail: {link}: {e}")

async def playwright_webscrape(context,link):
    pdf_links,img_links,links = [],[],[]
    page = await context.new_page()
    try:
        await page.goto(link,wait_until="load",timeout=15000)
        await asyncio.sleep(.5)

        # close popups/ads

        os.makedirs("scraped",exist_ok=True)
        title = await page.title()
        filename = f"untitled-{time.time()}" if title == '' else title
        valid_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ._-"
        filename = ''.join(char if char in valid_chars else '_' for char in filename)
        filename = filename[:255]
        with open(f"scraped/{filename}","w",encoding="utf-8") as file:
            pagebody = await page.wait_for_selector("body")
            file.write(await pagebody.inner_text())

        try:
            iframes = page.frames
            for iframe in iframes:
                await iframe.wait_for_load_state("load")
                framebody = await iframe.wait_for_selector("body")
                #print(iframe.url)
                #print(await framebody.inner_text())
        except: pass

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
        # ensure iframe data is sufficiently captured
        # put iframe data into saved html body data

        await page.screenshot(path=f"scraped/untitledscreenshot-{time.time()}.png" if title == '' else f"scraped/screenshot-{title}.png",full_page=True)

        return pdf_links,img_links,links
    except Exception as e:
        raise Exception(f"webscrape fail: {link}: {str(e).splitlines()[0]}")
    finally:
        await page.close()

async def webscrape_allowed(session,link):
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'}
    robots_url = urlparse(link).scheme+"://"+urlparse(link).netloc+"/robots.txt"
    rp = RobotFileParser()
    try:
        async with session.get(robots_url,headers=headers,timeout=10) as response:
            if response.status != 200:
                return f"robots.txt fail: {robots_url}: {response.status} {response.reason}"
            content = await response.text()
            rp.parse(content.splitlines())
            return rp.can_fetch("*",link)
    except Exception as e:
        return f"robots.txt fail: {robots_url}: {repr(e)}"

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
        raise Exception(f"google web search fail: '{params["q"]}': {e}")
    return [item["link"] for item in results.get("items",[])]

async def scrape_and_crawl_worker(session,context,queue,visited_links,visited_links_lock):
    while True:
        link = await queue.get()
        try:
            async with visited_links_lock:
                if link in visited_links:
                    continue
                else:
                    visited_links.add(link)
            allowed = await webscrape_allowed(session,link)
            if not allowed:
                continue
            else:
                if not isinstance(allowed,bool):
                    print(allowed)
                if ".pdf" in link.lower():
                    await readPDF(session,link)
                else:
                    pdf_links,img_links,links = await playwright_webscrape(context,link)
                    for pdf_link in pdf_links:
                        if not pdf_link in visited_links:
                            await queue.put(pdf_link)
                print(f"webscrape success: {link}")
        except Exception as e:
            print(e)
        finally:
            queue.task_done()

async def main():
    MAX_NUM_TASKS = 10
    links = google_web_search('Apple Financial Forecast',ws_apis['google']['API_KEY'],ws_apis['google']['CSE_ID'])
    queue = asyncio.Queue()
    visited_links = set()
    visited_links_lock = asyncio.Lock()
    for link in links:
        await queue.put(link)

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                "AppleWebKit/537.36 (KHTML, like Gecko)"
                "Chrome/114.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1366, "height": 768},
            locale="en-US",
            color_scheme="light",
            timezone_id="America/New_York",
            geolocation={"longitude": -73.935242, "latitude": 40.730610}, # New York City
            permissions=["geolocation"],
            device_scale_factor=1.0,
            is_mobile=False,
            has_touch=False,
            java_script_enabled=True,
        )
        async with aiohttp.ClientSession() as session:
            scrape_and_crawl_workers = []
            for _ in range(MAX_NUM_TASKS):
                scrape_and_crawl_workers.append(asyncio.create_task(scrape_and_crawl_worker(session,context,queue,visited_links,visited_links_lock)))
            await queue.join()

            for worker in scrape_and_crawl_workers:
                worker.cancel()
            await asyncio.gather(*scrape_and_crawl_workers,return_exceptions=True)
        await context.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())