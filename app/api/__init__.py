from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.documents import router as documents_router
from app.api.questions import router as questions_router
from app.api.answers import router as answers_router
from app.api.review import router as review_router
from app.api.export import router as export_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(documents_router)
api_router.include_router(questions_router)
api_router.include_router(answers_router)
api_router.include_router(review_router)
api_router.include_router(export_router)
