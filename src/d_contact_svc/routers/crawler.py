from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
import logging

from d_contact_svc.crawler import crawl_website

router = APIRouter()

class CrawlRequest(BaseModel):
    url: HttpUrl

@router.post("/crawl")
async def crawl_endpoint(request: CrawlRequest):
    try:
        # Call the crawl_website function with the validated URL
        results = crawl_website(str(request.url))
        return {"results": results}
    except Exception as e:
        logging.error(e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to crawl website")
