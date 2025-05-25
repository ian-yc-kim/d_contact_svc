from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
import logging

from d_contact_svc.crawler import crawl_website
from d_contact_svc.email_extractor import extract_emails
from d_contact_svc.ai_agent import identify_email_owners

router = APIRouter()

class CrawlRequest(BaseModel):
    url: HttpUrl

@router.post("/crawl")
async def crawl_endpoint(request: CrawlRequest):
    """
    Endpoint that crawls a given website URL, extracts emails and their contexts from the crawled HTML pages,
    identifies the email owner using an AI-driven service, and returns aggregated results.
    """
    try:
        # Step 1: Crawl website to get HTML page contents
        html_pages = crawl_website(str(request.url))

        # Step 2: For each HTML page, extract emails and accumulate results
        extraction_results = []
        for html in html_pages:
            extracted = extract_emails(html)
            extraction_results.extend(extracted)

        # If no emails are extracted, return empty results
        if not extraction_results:
            return {"results": []}

        # Step 3: Build a list of email contexts in the order of extraction
        email_contexts = [result["context"] for result in extraction_results]

        # Step 4: Identify email owners using AI for the list of email contexts
        ai_identifications = identify_email_owners(email_contexts)

        # Step 5: Merge extraction results with identification results
        aggregated_results = []
        for extraction, identification in zip(extraction_results, ai_identifications):
            aggregated_results.append({
                "email": extraction.get("email"),
                "owner_name": identification.get("owner")
            })

        return {"results": aggregated_results}
    except Exception as e:
        logging.error(e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to crawl website")
