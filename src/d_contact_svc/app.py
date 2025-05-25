from fastapi import FastAPI

app = FastAPI(debug=True)

# Include crawler router
from d_contact_svc.routers import crawler
app.include_router(crawler.router)
