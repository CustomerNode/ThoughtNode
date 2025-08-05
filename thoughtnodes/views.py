from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from .models import Thoughtnode
from . import forms
from playwright.async_api import async_playwright
from urllib.robotparser import RobotFileParser
from urllib.request import Request,urlopen
from urllib.parse import urlparse,urlunparse,quote
from PyPDF2 import PdfReader
from io import BytesIO
from openai import OpenAI
from celery import shared_task,chain
from asgiref.sync import async_to_sync
from redis import Redis as syncRedis
from redis.asyncio import Redis
from redis.asyncio.lock import Lock
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import requests
import asyncio
import aiohttp
import hashlib
import time
import os

# Create your views here.
@login_required(login_url='/profiles/login')
def thoughtnodes_list(request):
    thoughtnodes = Thoughtnode.objects.filter(user=request.user).order_by('-date')
    return render(request,'thoughtnodes/thoughtnodes_list.html',{'thoughtnodes':thoughtnodes})

@login_required(login_url='/profiles/login')
def thoughtnode_view(request,slug):
    thoughtnode = Thoughtnode.objects.get(slug=slug)
    return render(request,'thoughtnodes/thoughtnode_view.html',{'thoughtnode':thoughtnode})

@login_required(login_url='/profiles/login')
def thoughtnode_add(request):
    if(request.method == 'POST'):
        form = forms.CreateThoughtnode(request.POST)
        if(form.is_valid()):
            newthoughtnode = form.save(commit=False)
            newthoughtnode.user = request.user
            newthoughtnode.makeslug()
            newthoughtnode.save()
            return redirect('thoughtnodes:viewthoughtnode',newthoughtnode.slug)
    else:
        form = forms.CreateThoughtnode()
    return render(request,'thoughtnodes/thoughtnode_add.html',{'form':form})

@login_required(login_url='/profiles/login')
def thoughtnode_edit(request,slug):
    thoughtnode = Thoughtnode.objects.get(slug=slug)
    if(request.method == 'POST'):
        form = forms.CreateThoughtnode(request.POST,instance=thoughtnode)
        if(form.is_valid()):
            newthoughtnode = form.save(commit=False)
            newthoughtnode.save()
            return redirect('thoughtnodes:viewthoughtnode',newthoughtnode.slug)
    else:
        form = forms.CreateThoughtnode(instance=thoughtnode)
    return render(request,'thoughtnodes/thoughtnode_edit.html',{'form':form,'thoughtnode':thoughtnode})

@login_required(login_url='/profiles/login')
def thoughtnode_delete(request,slug):
    if(request.method == 'POST'):
        thoughtnode = Thoughtnode.objects.get(slug=slug)
        thoughtnode.delete()
        return redirect('thoughtnodes:thoughtnodeslist')

def thoughtnode_run(slug):
    thoughtnode = Thoughtnode.objects.get(slug=slug)
    chain(
        # Web search scrape and crawl
        celery_scrape_and_crawl.s(slug,thoughtnode.query),
        #ChatGPT Summarization/Analysis
        celery_chatgpt_summarize.s(slug),
        # Send Email
        celery_send_email.s(slug)
    )()
    print(f"thoughtnode (scrape,summarize,email) chain started: {slug}")

def sanitize_link(link):
    parsed = urlparse(link)
    clean_url = urlunparse(parsed._replace(fragment=""))
    return hashlib.sha256(clean_url.encode('utf-8')).hexdigest()

async def readPDF(session,link,r1,r2,id):
    try:
        async with session.get(link) as response:
            content = await response.read()
            pdf = PdfReader(BytesIO(content))
            pdfcontent = ''
            for i in range(len(pdf.pages)):
                pdfcontent += pdf.pages[i].extract_text()
            await r2.hset(id,sanitize_link(link),pdfcontent)
            for additionalid in await r2.hkeys("*"):
                if await r2.hexists(additionalid.decode(),sanitize_link(link)) and (await r2.hget(additionalid.decode(),sanitize_link(link))).decode() == "":
                    await r2.hset(id,sanitize_link(link),pdfcontent)
    except Exception as e:
        await r1.sadd("badsites",urlparse(link).scheme+"://"+urlparse(link).netloc)
        raise Exception(f"read pdf fail: {link}: {e}")

async def playwright_webscrape(context,link,r1,r2,id):
    pdf_links,img_links,links = [],[],[]
    page = await context.new_page()
    try:
        await page.goto(link,wait_until="load",timeout=15000)
        await asyncio.sleep(.5)

        # close popups/ads

        pagebody = await page.wait_for_selector("body")
        await r2.hset(id,sanitize_link(link),await pagebody.inner_text())
        for additionalid in await r2.hkeys("*"):
            if await r2.hexists(additionalid.decode(),sanitize_link(link)) and (await r2.hget(additionalid.decode(),sanitize_link(link))).decode() == "":
                await r2.hset(additionalid.decode(),sanitize_link(link),await pagebody.inner_text())

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

        # await page.screenshot(path=f"/scraped/screenshot-{filename}.png",full_page=True)

        return pdf_links,img_links,links
    except Exception as e:
        await r1.sadd("badsites",urlparse(link).scheme+"://"+urlparse(link).netloc)
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

async def duckduckgo_web_search(query,num_results=10):
    redis_url = os.getenv("REDIS_URL","redis://localhost:6379/1")
    r1 = Redis.from_url(redis_url)
    url = "https://duckduckgo.com/?q="
    query = query.replace(" ","+")
    url += query
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context(
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"),
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
        page = await context.new_page()
        await page.goto(url,wait_until="load",timeout=15000)
        await asyncio.sleep(.5)
        links = []
        while len(links) < num_results:
            pagebody = await page.wait_for_selector("body")
            await page.click("button[id='more-results']")
            bodylinks = await pagebody.query_selector("ol")
            urllinks = await bodylinks.query_selector_all("a")
            for link in urllinks:
                link = await link.get_attribute("href")
                if link is not None and link not in links and link[:4] == "http" and not await r1.sismember("badsites",urlparse(link).scheme+"://"+urlparse(link).netloc):
                    links.append(link)
        if len(links) > num_results:
            links = links[:num_results]
        await page.close()
        await context.close()
        await browser.close()
    return links

def google_web_search(query,api_key,cse_id,num_results=10):
    url = 'https://www.googleapis.com/customsearch/v1'
    params = {
        "q":query,
        "key":api_key,
        "cx":cse_id,
        "num":num_results
    }
    try:
        response = requests.get(url=url,params=params)
        response.raise_for_status()
        results = response.json()
    except Exception as e:
        raise Exception(f"google web search fail: '{params['q']}': {e}")
    return [item["link"] for item in results.get("items",[])]

async def scrape_and_crawl_worker(session,context,r1,r2,id,redislock,workerlock):
    while True:
        link = await r1.spop("scqueue")
        if not link:
            async with workerlock:
                await r1.decr("NUM_WORKERS")
            break
        link = link.decode()
        try:
            async with redislock:
                if await r1.sismember("visitedlinks",link):
                    for additionalid in await r2.keys("*"):
                        if await r2.hexists(additionalid.decode(),sanitize_link(link)):
                            additionalidval = (await r2.hget(additionalid.decode(),sanitize_link(link))).decode()
                            if additionalidval != "":
                                await r2.hset(id,sanitize_link(link),additionalidval)
                    continue
                else:
                    await r1.sadd("visitedlinks",link)
            allowed = await webscrape_allowed(session,link)
            if not allowed:
                await r1.sadd("badsites",urlparse(link).scheme+"://"+urlparse(link).netloc)
                continue
            else:
                if not isinstance(allowed,bool):
                    print(allowed)
                if ".pdf" in link.lower():
                    await readPDF(session,link,r1,r2,id)
                else:
                    pdf_links,img_links,links = await playwright_webscrape(context,link,r1,r2,id)
                    for pdf_link in pdf_links:
                        async with redislock:
                            if not await r1.sismember("visitedlinks",pdf_link):
                                await r1.sadd("scqueue",pdf_link)
                print(f"webscrape success: {link}")
        except Exception as e:
            print(e)

async def search_scrape_and_crawl_manager(id,query):
    redis_url = os.getenv("REDIS_URL","redis://localhost:6379/1")
    r1 = Redis.from_url(redis_url)
    redis_url = os.getenv("REDIS_URL","redis://localhost:6379/2")
    r2 = Redis.from_url(redis_url)
    redislock = Lock(r1,"redislock",timeout=10)
    workerlock = Lock(r1,"workerlock",timeout=10)
    async with workerlock:
        if not await r1.exists("MAX_NUM_WORKERS"):
            await r1.set("MAX_NUM_WORKERS",25)
        if not await r1.exists("NUM_WORKERS"):
            await r1.set("NUM_WORKERS",0)
    tasks = []

    links = []
    try:
        # links = google_web_search(query,os.getenv('GOOGLE_API_KEY'),os.getenv('GOOGLE_CSE_ID'))
        links = await duckduckgo_web_search(query)
        print(f"{id}: {links}")
    except Exception as e:
        print(e)
    for link in links:
        async with redislock:
            if await r1.sismember("visitedlinks",link):
                for additionalid in await r2.keys("*"):
                    if await r2.hexists(additionalid.decode(),sanitize_link(link)):
                        additionalidval = (await r2.hget(additionalid.decode(),sanitize_link(link))).decode()
                        if additionalidval != "":
                            await r2.hset(id,sanitize_link(link),additionalidval)
            elif await r1.sismember("scqueue",link):
                await r2.hset(id,sanitize_link(link),"")
            else:
                await r1.sadd("scqueue",link)
                print(f"link queued: {link}")
    if await r1.scard("scqueue") > 0:
        async with async_playwright() as p:
            browser = await p.firefox.launch(headless=True)
            context = await browser.new_context(
                user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"),
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
                async with workerlock:
                    numworkers = int((await r1.get("NUM_WORKERS")).decode())
                    maxworkers = int((await r1.get("MAX_NUM_WORKERS")).decode())
                    if numworkers + len(links) < maxworkers:
                        maxworkers = len(links)
                    while int((await r1.get("NUM_WORKERS")).decode()) < maxworkers:
                        await r1.incr("NUM_WORKERS")
                        tasks.append(asyncio.create_task(scrape_and_crawl_worker(session,context,r1,r2,id,redislock,workerlock)))
                await asyncio.gather(*tasks,return_exceptions=True)
            await context.close()
            await browser.close()
    valspopulated = 0
    while valspopulated != await r2.hlen(id):
        valspopulated = 0
        for val in await r2.hvals(id):
            if val.decode() != "":
                valspopulated += 1
        await asyncio.sleep(1)

@shared_task
def celery_scrape_and_crawl(id,query):
    async_to_sync(search_scrape_and_crawl_manager)(id,query)

@shared_task
def celery_chatgpt_summarize(_,id):
    redis_url = os.getenv("REDIS_URL","redis://localhost:6379/2")
    redisdata = syncRedis.from_url(redis_url)
    data = redisdata.hgetall(id)
    # client = OpenAI() # implement ChatGPT summarization
    return "summarization not yet implemented"

@shared_task
def celery_send_email(summarization,id):
    print(f"email sent: {id}: {Thoughtnode.objects.get(slug=id).user.email}")
    return
    thoughtnode = Thoughtnode.objects.get(id=id)
    user_email = thoughtnode.user.email
    message = Mail(
        from_email=os.environ.get("SENDGRID_FROM_EMAIL"),
        to_emails=user_email,
        subject=thoughtnode.title,
        plain_text_content=summarization,
        html_content=""
    )
    try:
        if user_email is not None or user_email != "":
            sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
            response = sg.send(message)
    except Exception as e:
        print(f"sendgrid fail: {e}")