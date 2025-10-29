from fastapi import FastAPI
from mini_ddq_app.routes import auth as auth_routes
from mini_ddq_app.routes import responses as response_routes
from mini_ddq_app.routes import questions as question_routes
from mini_ddq_app.routes import search as search_routes
from mini_ddq_app.routes import imports as imports_routes

app = FastAPI(title="Mini DDQ API")

app.include_router(auth_routes.router)
app.include_router(question_routes.router)
app.include_router(response_routes.router)
app.include_router(search_routes.router)
app.include_router(imports_routes.router)