#main.py
import asyncio
import sys
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from crawler import collect_all_links
if sys.platform.startswith("win"):
    #async operations
    try:
        policy = asyncio.WindowsProactorEventLoopPolicy()
        asyncio.set_event_loop_policy(policy)
        print("Set Windows ProactorEventLoopPolicy")
    except AttributeError:
        try:
            policy = asyncio.WindowsSelectorEventLoopPolicy()
            asyncio.set_event_loop_policy(policy)
            print("Set Windows SelectorEventLoopPolicy")
        except AttributeError:
            print("Using default event loop policy")
app = FastAPI()
class URLRequest(BaseModel):
    url: str
@app.post("/crawl")
async def crawl_website(request: URLRequest):
    try:
        loop = asyncio.get_event_loop()
        if sys.platform.startswith("win"):
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        all_links = await collect_all_links(request.url)
        return {"total_links": len(all_links), "links": all_links}
    except Exception as e:
        print(f"Error in crawl_website: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/")
async def root():
    return {"message": "Welcome to the web crawler API!"}