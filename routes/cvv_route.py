from fastapi import APIRouter

cvv_router = APIRouter(prefix="/cvv", tags=["cvv"])

@cvv_router.post("/create-cvv")

def create_cvv():
  return {"cvv": "cvv"}
