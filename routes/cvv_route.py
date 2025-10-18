from fastapi import APIRouter, HTTPException, status, UploadFile
from dtos.cvv_dto import CreateCVVDTO
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

cvv_router = APIRouter(prefix="/cvv", tags=["cvv"])

@cvv_router.post("/create-cvv", status_code=status.HTTP_200_OK)
async def create_cvv(dto: CreateCVVDTO):
    pdf_file = None
    try:
        pdf_file = dto.pdf_file
        
        if not pdf_file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O arquivo deve ser um PDF"
            )
        
        # Lê o conteúdo binário do PDF
        pdf_content = await pdf_file.read()
        
        # Verifica se o arquivo não está vazio
        if not pdf_content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O arquivo PDF está vazio"
            )
            
        # Verifica se é um PDF válido (os primeiros 4 bytes devem ser '%PDF')
        if not pdf_content.startswith(b'%PDF'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O arquivo não parece ser um PDF válido"
            )
        
        # Cria um diretório temporário se não existir
        os.makedirs("temp_uploads", exist_ok=True)
        
        # Salva o arquivo temporariamente (opcional)
        temp_path = os.path.join("temp_uploads", pdf_file.filename)
        with open(temp_path, "wb") as f:
            f.write(pdf_content)
        
        logger.info(f"Arquivo PDF recebido e salvo: {pdf_file.filename} ({len(pdf_content)} bytes)")
        
        return {
            "message": "Arquivo PDF recebido com sucesso!",
            "filename": pdf_file.filename,
            "size": len(pdf_content),
            "saved_path": temp_path
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao processar os arquivos: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar os arquivos: {str(e)}"
        )
    finally:
        if 'dto' in locals() and hasattr(dto, 'pdf_file') and dto.pdf_file:
            await dto.pdf_file.close()

