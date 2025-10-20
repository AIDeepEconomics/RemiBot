from fastapi import APIRouter

from . import config, logs, remitos, telefonos, webhook

router = APIRouter()

router.include_router(webhook.router, prefix="/webhook", tags=["webhook"])
router.include_router(remitos.router, prefix="/remitos", tags=["remitos"])
router.include_router(config.router, prefix="/config", tags=["config"])
router.include_router(logs.router, prefix="/logs", tags=["logs"])
router.include_router(telefonos.router, prefix="/telefonos", tags=["telefonos"])
