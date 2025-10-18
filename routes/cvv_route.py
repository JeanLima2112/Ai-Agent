from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain

from pathlib import Path
import tempfile

cvv_router = APIRouter(prefix="/cvv", tags=["cvv"])

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="models/gemini-2.5-flash",
    temperature=0,
    api_key=os.getenv("GOOGLE_API_KEY"),
)
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
)

# document_chain = create_stuff_documents_chain(llm, prompt=PROMPT) Criar o Prompt

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

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(await pdf_file.read())
            tmp_path = tmp.name

        loader = PyMuPDFLoader(tmp_path)
        docs = loader.load()
        print(f"Arquivo carregado: {pdf_file.filename}, {len(docs)} páginas")
        splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=30)
        chunks = splitter.split_documents(docs)
        print(f"Documentos divididos: {len(chunks)} chunks")

        

        # vectorstore = FAISS.from_documents(chunks, embeddings)
        # retriever = vectorstore.as_retriever(
        #     search_type="similarity_score_threshold",
        #     search_kwargs={"score_threshold": 0.3, "k": 4},
        # )

    except Exception as e:
        print(f"Erro ao carregar {pdf_file.filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar o PDF: {str(e)}"
        )
    finally:
        pdf_file.file.close()
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return {
        "filename": pdf_file.filename,
        "description": description,
        "pages_loaded": len(docs)
    }


    # return StreamingResponse(
    #     pdf_file.file,
    #     media_type="application/pdf",
    #     headers={"Content-Disposition": f'attachment; filename="{pdf_file.filename}"'}
    # )
