from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
import os

cvv_router = APIRouter(prefix="/cvv", tags=["cvv"])

load_dotenv()

# llm = ChatGoogleGenerativeAI(
#     model="models/gemini-2.5-flash",
#     temperature=0,
#     api_key=os.getenv("GOOGLE_API_KEY"),
# )

print(os.getenv("GOOGLE_API_KEY"))

@cvv_router.post("/create-cvv", status_code=status.HTTP_200_OK)
async def create_cvv(
    pdf_file: UploadFile = File(...),
    description: str = Form(...)
):
    if not pdf_file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O arquivo deve ser um PDF"
        )
    


    # return StreamingResponse(
    #     pdf_file.file,
    #     media_type="application/pdf",
    #     headers={"Content-Disposition": f'attachment; filename="{pdf_file.filename}"'}
    # )
