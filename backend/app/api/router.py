from fastapi import APIRouter

from .routes.health import router as health_router
from .routes.inspections import router as inspections_router
from .routes.model import router as model_router

router = APIRouter()
router.include_router(health_router)
router.include_router(inspections_router)
router.include_router(model_router)
