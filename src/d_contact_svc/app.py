from fastapi import FastAPI

app = FastAPI(debug=True)

# Include crawler router
from d_contact_svc.routers import crawler
app.include_router(crawler.router)

# Include AI Agent endpoint router
from d_contact_svc.routers import ai_agent_endpoint
app.include_router(ai_agent_endpoint.router)
