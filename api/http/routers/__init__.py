from fastapi import APIRouter

from api.http.routers.health import router as health_router
from api.http.routers.leech import router as leech_router

router = APIRouter()
router.include_router(health_router)
router.include_router(leech_router)

