from fastapi import APIRouter

from api.endpoints import audit, contracts

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(audit.router, tags=["audit"])
api_router.include_router(contracts.router, tags=["contracts"])
