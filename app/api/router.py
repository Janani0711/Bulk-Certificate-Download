from fastapi import APIRouter
from app.api.endpoints import jobs, certificates

api_router = APIRouter()
api_router.include_router(jobs.router)
api_router.include_router(certificates.router)
