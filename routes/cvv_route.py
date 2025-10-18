from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from dtos.cvv_dto import CreateCVVDTO

cvv_router = APIRouter(prefix="/cvv", tags=["cvv"])

@cvv_router.post("/create-cvv", status_code=status.HTTP_200_OK)
async def create_cvv(cvv_data: CreateCVVDTO):
    if not cvv_data.pdf_file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O arquivo deve ser um PDF"
        )

    return StreamingResponse(
        cvv_data.pdf_file.file,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{cvv_data.pdf_file.filename}"'}
    )
