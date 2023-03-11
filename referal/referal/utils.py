from rest_framework.routers import DefaultRouter
import logging

log = logging.getLogger(__name__)

DEFAULT_ROUTER = None


def get_default_router() -> DefaultRouter:
    log.debug("Retrieving default router")
    global DEFAULT_ROUTER

    if DEFAULT_ROUTER is None:
        log.debug("Default router hasn't been set, configuring")
        DEFAULT_ROUTER = DefaultRouter()

    return DEFAULT_ROUTER
