from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.schema import Document
from langchain_core.prompts import ChatPromptTemplate


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
PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Você é um redator de currículos de elite, especialista em marketing pessoal e otimização para ATS. Sua única missão é transformar o currículo fornecido em um documento de marketing de alto impacto, reescrevendo cada informação para que pareça o mais impressionante e valiosa possível, com o objetivo final de garantir a chamada para a entrevista.\n\n"
            "REGRAS DE TRANSFORMAÇÃO:\n"
            "1.  **Reenquadramento para Impacto**: Não liste responsabilidades, transforme-as em conquistas. Cada item de experiência deve responder à pergunta: 'Que valor ou resultado positivo eu gerei para a empresa?'. Ex: 'Fazia relatórios' se torna 'Desenvolvi relatórios analíticos que otimizaram a tomada de decisão da liderança em 15%'.\n"
            "2.  **Quantificação Agressiva**: Procure ativamente por qualquer oportunidade de adicionar números, percentagens, valores monetários ($) ou prazos. Se o currículo original não tiver métricas, use a sua expertise para inferir o impacto e insira placeholders estratégicos para o usuário confirmar. Ex: '[Confirmar: Aumento de aproximadamente 20-30% na eficiência]'.\n"
            "3.  **Linguagem de Liderança e Inovação**: Utilize um vocabulário poderoso e proativo. Prefira verbos que denotem liderança, iniciativa e melhoria contínua (ex: Orquestrei, Pioneirei, Revolucionei, Otimizei, Escalei, Implementei) em vez de verbos passivos (ex: Ajudei, Fui responsável por).\n"
            "4.  **Alinhamento Estratégico com a Vaga**: Analise a vaga para entender não só as palavras-chave, mas o 'problema' que a empresa quer resolver com essa contratação. Posicione o candidato como a solução direta para esse problema em todo o texto do currículo, especialmente no Resumo Profissional.\n"
            "5.  **Princípio da Excelência**: Assuma que todas as tarefas foram executadas com um alto grau de competência e descreva-as como tal. O objetivo é criar uma percepção de um profissional de alto desempenho."
        ),
        ("user", "Pergunta: {input}\n\nContexto:\n{context}"),
    ]
)
document_chain = create_stuff_documents_chain(llm, prompt=PROMPT)

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
        pdf_docs = loader.load()
        print(f"Arquivo carregado: {pdf_file.filename}, {len(pdf_docs)} páginas")

        desc_doc = Document(page_content=description)

        splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=30)
        pdf_chunks = splitter.split_documents(pdf_docs)
        desc_chunks = splitter.split_documents([desc_doc])

        print(f"Chunks do PDF: {len(pdf_chunks)}")
        print(f"Chunks da descrição: {len(desc_chunks)}")

        

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
        "pdf_chunks": len(pdf_chunks),
        "description_chunks": len(desc_chunks)
    }


    # return StreamingResponse(
    #     pdf_file.file,
    #     media_type="application/pdf",
    #     headers={"Content-Disposition": f'attachment; filename="{pdf_file.filename}"'}
    # )
