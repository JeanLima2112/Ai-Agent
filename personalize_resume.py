import argparse
import io
import os
from datetime import datetime
from pathlib import Path

import fitz  # PyMuPDF
from dotenv import load_dotenv
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate


PROMPT_CURRICULO = ChatPromptTemplate.from_messages(
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
        (
            "user",
            "Descrição completa da vaga (o problema que eles querem resolver):\n{vaga}\n\n"
            "Currículo original (os fatos brutos):\n{curriculo}\n\n"
            "Transforme este currículo em uma ferramenta de marketing pessoal de impacto máximo. A saída deve ser apenas o texto do currículo final, pronto para ser enviado, seguindo esta estrutura otimizada:\n\n"
            "**NOME COMPLETO**\n"
            "Cidade, Estado | Telefone | Email | Link do LinkedIn\n\n"
            "**RESUMO PROFISSIONAL**\n"
            "(Um parágrafo de 3-4 linhas que posiciona o candidato como a solução ideal para a vaga, destacando 2-3 conquistas quantificadas mais impressionantes e alinhadas aos requisitos.)\n\n"
            "**COMPETÊNCIAS ESTRATÉGICAS**\n"
            "(Uma lista com as 8-10 competências mais críticas para a vaga, combinando habilidades técnicas e ferramentas. Use os mesmos termos da descrição da vaga.)\n"
            "- Competência Chave 1 | Competência Chave 2 | Competência Chave 3\n"
            "- Ferramenta 1 | Ferramenta 2 | Ferramenta 3\n\n"
            "**HISTÓRICO DE CONQUISTAS PROFISSIONAIS**\n"
            "**Nome da Empresa**\n"
            "*Cargo Ocupado* | Mês/Ano de Início – Mês/Ano de Fim\n"
            "- Conquista de alto impacto: Comece com um verbo de ação poderoso e inclua uma métrica que demonstre o valor gerado.\n"
            "- Conquista de alto impacto: Descreva como uma tarefa rotineira foi otimizada ou melhorada, gerando economia de tempo ou dinheiro.\n"
            "- Conquista de alto impacto: Alinhe um projeto ou resultado diretamente com um requisito chave da nova vaga.\n\n"
            "**FORMAÇÃO ACADÊMICA**\n"
            "**Nome da Instituição** | *Nome do Curso*, Ano de Conclusão\n\n"
            "**CERTIFICAÇÕES E DESENVOLVIMENTO CONTÍNUO**\n"
            "(Liste apenas as certificações mais relevantes que reforçam a imagem de um especialista na área.)"
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


def _extract_pdf_text(pdf_path: Path) -> str:
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF não encontrado: {pdf_path}")
    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError("O caminho do currículo deve apontar para um arquivo .pdf")

    with fitz.open(pdf_path) as doc:
        texts = []
        for page in doc:
            texts.append(page.get_text())
    text = "\n".join(texts).strip()
    if not text:
        raise ValueError("Nenhum texto extraído do PDF.")
    return text


def _read_job_text(txt_path: Path) -> str:
    if not txt_path.exists():
        raise FileNotFoundError(f"TXT da vaga não encontrado: {txt_path}")
    return txt_path.read_text(encoding="utf-8").strip()


def _render_text_to_pdf(text: str, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    left_margin = 20 * mm
    right_margin = 20 * mm
    top_margin = 20 * mm
    bottom_margin = 20 * mm

    usable_width = width - left_margin - right_margin

    c.setFont("Helvetica", 10)

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
    line_height = 12

    for line in wrap_text(text, usable_width):
        if y <= bottom_margin:
            c.showPage()
            c.setFont("Helvetica", 10)
            y = height - top_margin
        if line == "":
            y -= line_height
            continue
        c.drawString(left_margin, y, line)
        y -= line_height

    c.showPage()
    c.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()
    out_path.write_bytes(pdf_bytes)


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Personaliza um currículo PDF com base em uma descrição de vaga em TXT e gera um novo PDF."
    )
    parser.add_argument("--curriculo", required=True, help="Caminho para o PDF do currículo")
    parser.add_argument("--vaga", required=True, help="Caminho para o arquivo TXT com a descrição da vaga")
    parser.add_argument("--out", default=None, help="Caminho do PDF de saída (opcional)")
    parser.add_argument("--model", default="models/gemini-2.5-flash", help="Modelo Gemini a ser usado")
    parser.add_argument("--temperature", type=float, default=0.3, help="Temperatura do LLM")

    args = parser.parse_args()

    pdf_path = Path(args.curriculo)
    vaga_path = Path(args.vaga)
    out_path = (
        Path(args.out)
        if args.out
        else Path(f"curriculo_personalizado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
    )

    # Extração e leitura
    curriculo_texto = _extract_pdf_text(pdf_path)
    vaga_texto = _read_job_text(vaga_path)

    # LLM
    api_key = os.getenv("GEMINIAI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("Defina GEMINIAI_API_KEY (ou GOOGLE_API_KEY) no .env para gerar o currículo.")
    llm = ChatGoogleGenerativeAI(model=args.model, temperature=args.temperature, api_key=api_key)

    prompt = PROMPT_CURRICULO.format_messages(vaga=vaga_texto, curriculo=curriculo_texto)
    resposta = llm.invoke(prompt)
    texto_final = (resposta.content or "").strip()

    if not texto_final:
        raise RuntimeError("Não foi possível gerar o currículo a partir do LLM.")

    # Gerar PDF
    _render_text_to_pdf(texto_final, out_path)

    print(f"Currículo personalizado gerado em: {out_path.resolve()}")


if __name__ == "__main__":
    main()
