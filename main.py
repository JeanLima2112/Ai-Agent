from pathlib import Path
from typing import Dict

from dotenv import load_dotenv
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain



PROMPT_RAG = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Você é um assistente útil que ajuda a responder perguntas sobre quesitos de Ética. "
            "Se você não souber a resposta, diga 'Não sei'. "
            "Não invente uma resposta.\n\n",
        ),
        ("user", "Pergunta: {input}\n\nContexto:\n{context}"),
    ]
)


load_dotenv()
GEMINIAI_API_KEY = Path(".env").read_text().split("=")[-1].strip()

llm = ChatGoogleGenerativeAI(
    model="models/gemini-2.5-flash",
    temperature=0,
    api_key=GEMINIAI_API_KEY,
)

document_chain = create_stuff_documents_chain(llm, prompt=PROMPT_RAG)


docs = []
for n in Path("./docs").glob("*.pdf"):
    try:
        loader = PyMuPDFLoader(str(n))
        docs.extend(loader.load())
        print(f"Arquivo carregado: {n.name}")
    except Exception as e:
        print(f"Erro ao carregar {n.name}: {e}")

print(f"Total de documentos carregados: {len(docs)}")


splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=30)
chunks = splitter.split_documents(docs)


embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=GEMINIAI_API_KEY,
)

vectorstore = FAISS.from_documents(chunks, embeddings)
retriever = vectorstore.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"score_threshold": 0.3, "k": 4},
)


def answer_question(question: str) -> Dict:
    docs_relevant = retriever.invoke(question)

    if not docs_relevant:
        return {"answer": "Não sei", "citations": [], "context": False}

    answer = document_chain.invoke(
        {"input": question, "context": docs_relevant}
    )

    txt = (answer or "").strip()

    if txt.rstrip(".!?").lower() == "não sei":
        return {"answer": txt, "citations": [], "context": False}

    return {"answer": txt, "citations": docs_relevant, "context": True}



testes = [
    "O que é ética e por que é importante na sociedade?",
    "Quais são os principais ramos da ética filosófica?",
    "Como a ética se aplica na tomada de decisões profissionais?",
    "Qual é a diferença entre ética e moralidade?",
    "Quais são alguns dilemas éticos comuns enfrentados na vida cotidiana?",
]

for pergunta in testes:
    resposta = answer_question(pergunta)
    print(f"Pergunta: {pergunta}")
    print(f"Resposta: {resposta['answer']}")
    if resposta["context"]:
        print("Citações encontradas:")
        for doc in resposta["citations"]:
            print(f"- {doc.metadata.get('source', 'Documento sem fonte')}")
    print("-" * 50)
