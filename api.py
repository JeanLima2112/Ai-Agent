import io
import os
from datetime import datetime
from typing import Optional

import fitz  # PyMuPDF
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate


load_dotenv()

app = FastAPI(title="WorkReadyAI - Personalizador de Currículo")


PROMPT_CURRICULO = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Você é um assistente especialista em RH que reescreve e estrutura currículos de forma clara, sucinta e orientada à vaga. \n"
            "Mantenha fatos verdadeiros do currículo original, reorganize e destaque experiências e resultados relevantes para a vaga. \n"
            "Use linguagem profissional em pt-BR, tópicos com bullet points quando apropriado e inclua um resumo profissional no topo. \n"
            "Se faltar informação essencial, preencha com placeholders TODO para o usuário revisar (ex.: 'TODO: adicionar link do LinkedIn')."
        ),
        (
            "user",
            "Dados da vaga (descrição completa):\n{vaga}\n\n"
            "Currículo original (texto extraído do PDF):\n{curriculo}\n\n"
            "Produza um currículo pronto para impressão, com as seguintes seções (apenas se fizerem sentido):\n"
            "- Cabeçalho: Nome completo, contato, cidade/UF\n"
            "- Resumo profissional (3-5 linhas)\n"
            "- Competências principais (bullet points)\n"
            "- Experiência profissional (empresa, cargo, período, responsabilidades e resultados)\n"
            "- Formação acadêmica\n"
            "- Certificações e cursos\n"
            "- Projetos/Portfólio (se aplicável)\n"
            "A saída deve ser apenas o conteúdo textual do currículo final, sem marcação, sem explicações."
        ),
    ]
)


def _get_llm() -> ChatGoogleGenerativeAI:
    api_key = os.getenv("GEMINIAI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Defina GEMINIAI_API_KEY (ou GOOGLE_API_KEY) no .env para gerar o currículo."
        )
    return ChatGoogleGenerativeAI(
        model="models/gemini-2.5-flash",
        temperature=0.3,
        api_key=api_key,
    )


@app.get("/health")
async def health():
    return JSONResponse({"status": "ok", "time": datetime.utcnow().isoformat()})


def _extract_pdf_text(file_bytes: bytes) -> str:
    try:
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            texts = []
            for page in doc:
                texts.append(page.get_text())
        text = "\n".join(texts).strip()
        if not text:
            raise ValueError("Nenhum texto extraído do PDF.")
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao ler PDF: {e}")


def _render_text_to_pdf(text: str) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    left_margin = 20 * mm
    right_margin = 20 * mm
    top_margin = 20 * mm
    bottom_margin = 20 * mm

    usable_width = width - left_margin - right_margin

    # Config fonte
    c.setFont("Helvetica", 10)

    # Word wrap simples
    def wrap_text(txt: str, max_width: float):
        lines = []
        for raw_line in txt.splitlines():
            line = raw_line.strip("\r")
            if not line:
                lines.append("")
                continue
            words = line.split()
            cur = []
            for w in words:
                candidate = (" ".join(cur + [w])).strip()
                if c.stringWidth(candidate, "Helvetica", 10) <= max_width:
                    cur.append(w)
                else:
                    lines.append(" ".join(cur))
                    cur = [w]
            if cur:
                lines.append(" ".join(cur))
        return lines

    y = height - top_margin
    line_height = 12  # pontos

    for line in wrap_text(text, usable_width):
        if y <= bottom_margin:
            c.showPage()
            c.setFont("Helvetica", 10)
            y = height - top_margin
        if line == "":
            y -= line_height  # linha em branco
            continue
        c.drawString(left_margin, y, line)
        y -= line_height

    c.showPage()
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


@app.post("/curriculo/personalizar")
async def personalizar_curriculo(
    arquivo: UploadFile = File(..., description="Envie um PDF de currículo"),
    vaga: str = Form(..., description="Cole a descrição completa da vaga"),
    nome_arquivo_saida: Optional[str] = Form(None, description="Nome do PDF de saída (opcional)"),
):
    if arquivo.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="O arquivo deve ser um PDF.")

    file_bytes = await arquivo.read()
    curriculo_texto = _extract_pdf_text(file_bytes)

    llm = _get_llm()
    prompt = PROMPT_CURRICULO.format_messages(vaga=vaga, curriculo=curriculo_texto)
    resposta = llm.invoke(prompt)
    texto_final = (resposta.content or "").strip()

    if not texto_final:
        raise HTTPException(status_code=500, detail="Não foi possível gerar o currículo.")

    pdf_bytes = _render_text_to_pdf(texto_final)

    saida_nome = nome_arquivo_saida or f"curriculo_personalizado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=\"{saida_nome}\""
        },
    )
