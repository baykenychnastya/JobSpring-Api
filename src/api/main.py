from fastapi import APIRouter

from api.routes import processing, calendar, email

api_router = APIRouter()

api_router.include_router(processing.router)
api_router.include_router(calendar.router)
api_router.include_router(email.router)
