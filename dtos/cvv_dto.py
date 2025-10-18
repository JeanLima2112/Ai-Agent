from fastapi import UploadFile, File, Form
from typing import Annotated

class CreateCVVDTO:
    pdf_file: Annotated[UploadFile, File(..., description="Arquivo PDF contendo o currículo")]
    description: Annotated[str, Form(..., description="Descrição do vaga")]
