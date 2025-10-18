from fastapi import APIRouter, UploadFile, HTTPException, status
from fastapi.responses import StreamingResponse

cvv_router = APIRouter(prefix="/cvv", tags=["cvv"])

@cvv_router.post("/create-cvv", status_code=status.HTTP_200_OK)
async def create_cvv(pdf_file: UploadFile):
    if not pdf_file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O arquivo deve ser um PDF"
        )

    return StreamingResponse(
        pdf_file.file,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{pdf_file.filename}"'}
    )
