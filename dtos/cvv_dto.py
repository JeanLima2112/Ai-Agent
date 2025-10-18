
from typing import Annotated
from fastapi import UploadFile, File
from pydantic import BaseModel


class CreateCVVDTO(BaseModel):
    pdf_file: Annotated[UploadFile, File(..., description="Arquivo PDF contendo o currículo")]
    
    class Config:
        json_schema_extra = {
            "example": {
                "pdf_file": "curriculo.pdf"
            }
        }
