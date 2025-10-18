from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from routes.cvv_route import cvv_router

app = FastAPI(title="FastAPI")

app.include_router(cvv_router)

@app.get("/")
def read_root():
  return {"hello": "world"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)