from fastapi import FastAPI
from routes import auth_router

app = FastAPI()

app.include_router(auth_router)