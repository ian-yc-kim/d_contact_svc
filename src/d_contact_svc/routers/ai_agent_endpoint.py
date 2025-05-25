from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from d_contact_svc.ai_agent import identify_email_owners

router = APIRouter()

class EmailContextsRequest(BaseModel):
    email_contexts: List[str]

@router.post("/identify-email-owner")
async def identify_email_owner_endpoint(payload: EmailContextsRequest):
    try:
        results = identify_email_owners(payload.email_contexts)
    except Exception as e:
        # Log error internally if needed
        raise HTTPException(status_code=500, detail="Internal Server Error")
    return {"results": results}
