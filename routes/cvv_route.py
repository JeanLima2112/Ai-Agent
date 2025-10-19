import os
from io import BytesIO
import tempfile
from typing import Dict, Any, Optional
import fitz 

from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

cvv_router = APIRouter(prefix="/cvv", tags=["cvv"])
load_dotenv()

LLM = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=1,
    api_key=os.getenv("GOOGLE_API_KEY"),
)

PROMPT_IA = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Você é um redator de currículos de elite, especialista em marketing pessoal e otimização para ATS. Sua única missão é transformar o currículo fornecido em um documento de marketing de alto impacto, reescrevendo cada informação para que pareça o mais impressionante e valiosa possível, com o objetivo final de garantir a chamada para a entrevista.\n\n"
            "REGRAS DE TRANSFORMAÇÃO:\n"
            "1.  **Reenquadramento para Impacto**: Não liste responsabilidades, transforme-as em conquistas. Cada item de experiência deve responder à pergunta: 'Que valor ou resultado positivo eu gerei para a empresa?'. Ex: 'Fazia relatórios' se torna 'Desenvolvi relatórios analíticos que otimizaram a tomada de decisão da liderança em 15%'.\n"
            "2.  **Quantificação Agressiva**: Procure ativamente por qualquer oportunidade de adicionar números, percentagens, valores monetários ($) ou prazos. Se o currículo original não tiver métricas, use a sua expertise para inferir o impacto.\n"
            "3.  **Linguagem de Liderança e Inovação**: Utilize um vocabulário poderoso e proativo. Prefira verbos que denotem liderança, iniciativa e melhoria contínua (ex: Orquestrei, Pioneirei, Revolucionei, Otimizei, Escalei, Implementei) em vez de verbos passivos (ex: Ajudei, Fui responsável por).\n"
            "4.  **Alinhamento Estratégico com a Vaga**: Analise a vaga para entender não só as palavras-chave, mas o 'problema' que a empresa quer resolver com essa contratação. Posicione o candidato como a solução direta para esse problema em todo o texto do currículo, especialmente no Resumo Profissional.\n"
            "5.  **Comunicação Clara e Profissional**:\n"
            "    - NUNCA inclua placeholders, colchetes ou textos entre parênteses para preenchimento futuro\n"
            "    - NÃO use expressões como 'a confirmar', 'a ser preenchido', 'informações a seguir' ou similares\n"
            "    - Se não tiver informações suficientes, descreva de forma genérica sem mencionar a falta de dados\n"
            "    - Mantenha um tom profissional e assertivo em todas as descrições\n"
            "6.  **Alinhamento com a Vaga**: Garanta que as exigências da vaga sejam claramente destacadas e que o currículo mostre como o candidato atende a elas.\n"
            "7.  **Tecnologias e tempo de experiência**: Garanta que as tecnologias e o tempo de experiência que costam na descrição da vaga sejam atendidos.\n"
            "**ESTRUTURA DE SAÍDA OBRIGATÓRIA (use EXATAMENTE este formato):**\n\n"
            "NOME: [Nome Completo do Candidato]\n\n"
            "CARGO: [Cargo Principal ou Desejado]\n\n"
            "RESUMO: [Parágrafo único e conciso do resumo profissional.]\n\n"
            "EXPERIENCIA:\n"
            "- [Cargo] | [Empresa] | [Período]\n"
            "  - [Descrição da primeira conquista ou responsabilidade]\n"
            "  - [Descrição da segunda conquista]\n\n"
            "COMPETENCIAS:\n"
            "- [Categoria 1]: [Tecnologia 1], [Tecnologia 2]\n"
            "- [Categoria 2]: [Tecnologia 1], [Tecnologia 2]\n\n"
            "FORMACAO:\n"
            "- [Curso] | [Instituição] | [Período]\n\n"
            "CONTATO:\n"
            "- Telefone: [Seu Telefone]\n"
            "- Email: [Seu Email]\n"
            "- LinkedIn: [Seu LinkedIn]\n"
            "- GitHub: [Seu GitHub]"
        ),
        ("user", "Extraia e reescreva o currículo a seguir, seguindo a estrutura definida.\n\nCURRÍCULO ORIGINAL:\n{context}\n\nVAGA DESCRITA:\n{input}"),
    ]
)

DOCUMENT_CHAIN = create_stuff_documents_chain(LLM, PROMPT_IA)

def gerar_conteudo_otimizado(file_content: bytes, description: str) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file_content)
        tmp_path = tmp.name
    try:
        loader = PyMuPDFLoader(tmp_path)
        pdf_docs = loader.load()
        if not pdf_docs or not any(doc.page_content.strip() for doc in pdf_docs):
             raise ValueError("Nenhum conteúdo válido foi extraído do PDF.")
        return DOCUMENT_CHAIN.invoke({"input": description, "context": pdf_docs})
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

def parse_resposta_ia(texto_ia: str) -> Dict[str, Any]:
    data = {
        "NOME": "",
        "CARGO": "",
        "RESUMO": "",
        "EXPERIENCIA": [],
        "FORMACAO": [],
        "COMPETENCIAS": [],
        "CONTATO": []
    }
    
    if not texto_ia or not isinstance(texto_ia, str) or not texto_ia.strip():
        return data
    
    current_section = None
    
    try:
        for line in texto_ia.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
            
            if ":" in line:
                key_part = line.split(":", 1)[0].strip().upper()
                if key_part in ["NOME", "CARGO", "RESUMO"]:
                    key = key_part
                    value = line.split(":", 1)[1].strip()
                    if value:
                        data[key] = value
                    current_section = None
                    continue
            
            if line.endswith(':'):
                section_name = line[:-1].strip().upper()
                section_map = {
                    "EXPERIENCIA": "EXPERIENCIA",
                    "EXPERIÊNCIA": "EXPERIENCIA",
                    "EXPERIÊNCIAS": "EXPERIENCIA",
                    "FORMAÇÃO": "FORMACAO",
                    "FORMACAO": "FORMACAO",
                    "FORMAÇÕES": "FORMACAO",
                    "COMPETENCIA": "COMPETENCIAS",
                    "COMPETÊNCIA": "COMPETENCIAS",
                    "COMPETENCIAS": "COMPETENCIAS",
                    "COMPETÊNCIAS": "COMPETENCIAS",
                    "HABILIDADES": "COMPETENCIAS",
                    "CONTATO": "CONTATO",
                    "CONTATOS": "CONTATO"
                }
                current_section = section_map.get(section_name, None)
                continue
            
            if current_section and current_section in data:
                content = line.lstrip('-•* ').strip()
                if not content:
                    continue
                
                if current_section == "EXPERIENCIA":
                    if "|" in content:
                        data[current_section].append({
                            "titulo": content.strip(),
                            "detalhes": []
                        })
                    elif data[current_section] and isinstance(data[current_section][-1], dict):
                        if "detalhes" in data[current_section][-1]:
                            data[current_section][-1]["detalhes"].append(content)
                else:
                    if content not in data[current_section]:
                        data[current_section].append(content)
        
        for exp in data["EXPERIENCIA"]:
            if isinstance(exp, dict) and "detalhes" not in exp:
                exp["detalhes"] = []
        
        for key in ["NOME", "CARGO", "RESUMO"]:
            if key in data and not data[key]:
                data[key] = ""
                
        for key in ["EXPERIENCIA", "FORMACAO", "COMPETENCIAS", "CONTATO"]:
            if key in data and isinstance(data[key], list):
                if key == "EXPERIENCIA":
                    data[key] = [
                        exp for exp in data[key] 
                        if isinstance(exp, dict) and 
                           (exp.get("titulo") or exp.get("detalhes"))
                    ]
                else:
                    data[key] = [item for item in data[key] if item and str(item).strip()]
        
        return data
        
    except Exception as e:
        print(f"Erro ao processar resposta da IA: {e}")
        return data

def criar_pdf_estilizado_cv(dados_cv: Dict[str, Any]) -> BytesIO:
    try:
        print("\n=== DADOS RECEBIDOS PARA GERAÇÃO DO PDF ===")
        print(f"Tipo dos dados: {type(dados_cv)}")
        print(f"Chaves disponíveis: {list(dados_cv.keys())}")
        
        doc = fitz.open()
        
        margem = 40
        espacamento = 12
        fonte_normal = "helv"
        fonte_negrito = "hebo"
        
        largura = 595
        altura = 842
        
        cor_titulo = (0.2, 0.4, 0.8)
        cor_texto = (0.2, 0.2, 0.2)
        cor_fundo = (0.98, 0.98, 1.0)
        
        page = doc.new_page(width=largura, height=altura)
        
        def adicionar_texto(x, y, texto, fonte, tamanho, cor, negrito=False):
            nonlocal page
            try:
                if not texto or not str(texto).strip():
                    return y
                    
                max_caracteres = 110
                linhas = []
                texto = str(texto).strip()
                
                while len(texto) > max_caracteres:
                    quebra = texto[:max_caracteres].rfind(' ')
                    if quebra == -1:
                        quebra = max_caracteres
                    linhas.append(texto[:quebra].strip())
                    texto = texto[quebra:].strip()
                if texto:
                    linhas.append(texto)
                
                for linha in linhas:
                    if y > altura - margem - tamanho:
                        page = doc.new_page(width=largura, height=altura)
                        y = margem
                    
                    fonte_atual = fonte_negrito if negrito else fonte
                    
                    page.insert_text(
                        (x, y + tamanho * 0.8),
                        linha,
                        fontname=fonte_atual,
                        fontsize=tamanho,
                        color=cor
                    )
                    y += tamanho * 1.2
                
                return y
                
            except Exception as e:
                print(f"Erro ao adicionar texto: {e}")
                return y + tamanho * 1.2
        
        y_pos = margem
        
        if dados_cv.get("NOME"):
            nome = str(dados_cv["NOME"]).upper()
            print(f"\n--- ADICIONANDO NOME ---")
            print(f"Conteúdo: {nome}")
            
            y_pos = adicionar_texto(
                margem, y_pos,
                nome,
                fonte_negrito, 24, cor_titulo, True
            )
            
            # Linha horizontal abaixo do nome (mais grossa e mais longa)
            line_width = 1.5  # Aumentando a espessura da linha
            line_length = 500  # Aumentando o comprimento da linha
            
            # Desenha uma linha mais grossa para melhor visibilidade
            page.draw_line(
                (margem, y_pos - 5),
                (margem + line_length, y_pos - 5),
                color=cor_titulo,
                width=line_width
            )
            y_pos += 15  # Aumentando o espaçamento após a linha
        
        # Seção de Cargo
        if dados_cv.get("CARGO"):
            cargo = str(dados_cv["CARGO"])
            print(f"\n--- ADICIONANDO CARGO ---")
            print(f"Conteúdo: {cargo}")
            
            y_pos = adicionar_texto(
                margem, y_pos,
                cargo,
                fonte_negrito, 14, (0.3, 0.3, 0.5), True
            )
            y_pos += espacamento
        
        # Seção de Contato
        if dados_cv.get("CONTATO"):
            contato = dados_cv["CONTATO"]
            print(f"\n--- ADICIONANDO CONTATO ---")
            print(f"Tipo do contato: {type(contato)}")
            
            if isinstance(contato, list):
                print(f"Lista de contatos: {contato}")
                contato = " | ".join([str(c).strip() for c in contato if str(c).strip()])
            
            print(f"Texto do contato: {contato}")
            
            y_pos = adicionar_texto(
                margem, y_pos,
                str(contato),
                fonte_normal, 10, cor_texto
            )
            y_pos += espacamento
        
        page.draw_line(
            (margem, y_pos),
            (largura - margem, y_pos),
            color=(0.8, 0.8, 0.8),
            width=0.5
        )
        y_pos += espacamento
        
        # Seção de Resumo Profissional
        if dados_cv.get("RESUMO"):
            resumo = str(dados_cv["RESUMO"])
            print(f"\n--- ADICIONANDO RESUMO PROFISSIONAL ---")
            print(f"Tamanho do resumo: {len(resumo)} caracteres")
            print(f"Amostra: {resumo[:100]}..." if len(resumo) > 100 else f"Conteúdo: {resumo}")
            
            y_pos = adicionar_texto(
                margem, y_pos,
                "RESUMO PROFISSIONAL",
                fonte_negrito, 12, cor_titulo, True
            )
            
            y_pos = adicionar_texto(
                margem, y_pos,
                resumo,
                fonte_normal, 10, cor_texto
            )
            y_pos += espacamento
        
        # Seção de Experiência Profissional
        if dados_cv.get("EXPERIENCIA"):
            print(f"\n--- ADICIONANDO EXPERIÊNCIA PROFISSIONAL ---")
            
            # Garante que é uma lista
            experiencias = dados_cv["EXPERIENCIA"]
            if not isinstance(experiencias, list):
                experiencias = [experiencias]
                
            print(f"Número de experiências: {len(experiencias)}")
            
            y_pos = adicionar_texto(
                margem, y_pos,
                "EXPERIÊNCIA PROFISSIONAL",
                fonte_negrito, 12, cor_titulo, True
            )
            
            for idx, exp in enumerate(experiencias, 1):
                if not exp:
                    print(f"  Experiência {idx}: Dados vazios")
                    continue
                    
                print(f"\n  Experiência {idx}:")
                print(f"  Tipo: {type(exp)}")
                print(f"  Conteúdo: {exp}")
                
                # Se for string, tenta converter para dicionário
                if isinstance(exp, str):
                    exp = {"titulo": exp, "detalhes": []}
                # Se não for dicionário, pula para o próximo
                elif not isinstance(exp, dict):
                    print(f"  Experiência {idx}: Formato não suportado")
                    continue
                
                # Extrai título da experiência
                cabecalho = []
                if exp.get("titulo"):
                    cabecalho.append(str(exp["titulo"]).strip())
                elif exp.get("cargo"):
                    cabecalho.append(str(exp["cargo"]).strip())
                    if exp.get("empresa"):
                        cabecalho.append(str(exp["empresa"]).strip())
                    if exp.get("periodo"):
                        cabecalho.append(f"({str(exp['periodo']).strip()})")
                
                if cabecalho:
                    y_pos = adicionar_texto(
                        margem, y_pos,
                        " • ".join(cabecalho),
                        fonte_negrito, 10.5, cor_texto, True
                    )
                
                # Processa os detalhes da experiência
                if exp.get("detalhes") and isinstance(exp["detalhes"], list):
                    print(f"  Número de detalhes: {len(exp['detalhes'])}")
                    for detalhe in exp["detalhes"]:
                        if not detalhe:
                            continue
                            
                        print(f"  Processando detalhe: {detalhe[:100]}...")
                        
                        # Quebra o texto em linhas menores se for muito grande
                        texto = str(detalhe).strip()
                        linhas = []
                        while len(texto) > 150:  # Quebra em linhas de até 150 caracteres
                            espaco = texto[:150].rfind(' ')
                            if espaco == -1:
                                espaco = 150
                            linhas.append(texto[:espaco])
                            texto = texto[espaco:].strip()
                        if texto:
                            linhas.append(texto)
                        
                        # Adiciona cada linha com recuo
                        for i, linha in enumerate(linhas):
                            prefixo = "• " if i == 0 else "  "  # Só coloca o marcador na primeira linha
                            y_pos = adicionar_texto(
                                margem + 20, y_pos,
                                f"{prefixo}{linha}",
                                fonte_normal, 10, cor_texto
                            )
                            y_pos += 5  # Espaço entre linhas
                        
                        y_pos += 2  # Espaço entre itens
                
                y_pos += 5  # Espaço após a seção de experiência
        
        # Seção de Formação Acadêmica
        if dados_cv.get("FORMACAO"):
            print(f"\n--- ADICIONANDO FORMAÇÃO ACADÊMICA ---")
            
            # Garante que é uma lista
            formacoes = dados_cv["FORMACAO"]
            if not isinstance(formacoes, list):
                formacoes = [formacoes]
                
            print(f"Número de formações: {len(formacoes)}")
            
            y_pos = adicionar_texto(
                margem, y_pos,
                "FORMAÇÃO ACADÊMICA",
                fonte_negrito, 12, cor_titulo, True
            )
            
            for idx, form in enumerate(formacoes, 1):
                if not form:
                    print(f"  Formação {idx}: Dados vazios")
                    continue
                    
                print(f"\n  Formação {idx}:")
                print(f"  Tipo: {type(form)}")
                print(f"  Conteúdo: {form}")
                
                # Se for string, usa como está
                if isinstance(form, str):
                    y_pos = adicionar_texto(
                        margem, y_pos,
                        f"• {form}",
                        fonte_normal, 10, cor_texto
                    )
                    y_pos += 3
                    continue
                # Se for dicionário, processa os campos
                elif isinstance(form, dict):
                    linha = []
                    if form.get("curso"):
                        linha.append(str(form["curso"]).strip())
                    if form.get("instituicao"):
                        linha.append(str(form["instituicao"]).strip())
                    if form.get("periodo"):
                        linha.append(f"({str(form['periodo']).strip()})")
                    
                    if linha:
                        y_pos = adicionar_texto(
                            margem, y_pos,
                            f"• {' • '.join(linha)}",
                            fonte_normal, 10, cor_texto
                        )
                        
                        # Adiciona descrição se existir
                        if form.get("descricao"):
                            y_pos = adicionar_texto(
                                margem + 10, y_pos,
                                str(form["descricao"]).strip(),
                                fonte_normal, 9, (0.4, 0.4, 0.4)
                            )
                        
                        y_pos += 3
                else:
                    print(f"  Formação {idx}: Formato não suportado")
                
                linha = []
                if form.get("curso"):
                    linha.append(str(form["curso"]).strip())
                if form.get("instituicao"):
                    linha.append(str(form["instituicao"]).strip())
                if form.get("periodo"):
                    linha.append(f"({str(form['periodo']).strip()})")
                
                if linha:
                    y_pos = adicionar_texto(
                        margem, y_pos,
                        " • ".join(linha),
                        fonte_normal, 10, cor_texto
                    )
                
                if form.get("descricao"):
                    y_pos = adicionar_texto(
                        margem + 10, y_pos,
                        str(form["descricao"]).strip(),
                        fonte_normal, 9, (0.4, 0.4, 0.4)
                    )
                
                y_pos += 3
        
        # Seção de Competências
        if dados_cv.get("COMPETENCIAS"):
            print(f"\n--- ADICIONANDO HABILIDADES ---")
            
            competencias = dados_cv["COMPETENCIAS"]
            print(f"Tipo das competências: {type(competencias)}")
            
            if isinstance(competencias, str):
                print(f"Competências como string: {competencias}")
                competencias = [competencias]
            elif isinstance(competencias, list):
                print(f"Número de competências: {len(competencias)}")
                print(f"Competências: {competencias}")
            
            y_pos = adicionar_texto(
                margem, y_pos,
                "HABILIDADES",
                fonte_negrito, 12, cor_titulo, True
            )
            
            linha_atual = []
            linha_comprimento = 0
            
            for competencia in competencias:
                competencia = str(competencia).strip()
                if not competencia:
                    continue
                
                competencia = f"• {competencia}"
                
                if linha_atual and linha_comprimento + len(competencia) > 60:
                    y_pos = adicionar_texto(
                        margem, y_pos,
                        "  ".join(linha_atual),
                        fonte_normal, 10, cor_texto
                    )
                    linha_atual = []
                    linha_comprimento = 0
                
                linha_atual.append(competencia)
                linha_comprimento += len(competencia) + 2  
            
            if linha_atual:
                y_pos = adicionar_texto(
                    margem, y_pos,
                    "  ".join(linha_atual),
                    fonte_normal, 10, cor_texto
                )
            
            y_pos += espacamento
        
        # Gerando o PDF final
        print("\n=== GERANDO PDF FINAL ===")
        pdf_buffer = BytesIO()
        doc.save(pdf_buffer)
        pdf_buffer.seek(0)
        
        print(f"Tamanho do PDF gerado: {len(pdf_buffer.getvalue())} bytes")
        return pdf_buffer
        
    except Exception as e:
        print(f"Erro ao gerar PDF: {e}")
        raise ValueError(f"Erro ao processar o currículo: {str(e)}")
        
    finally:
        try:
            doc.close()
        except:
            pass

@cvv_router.post("/create-cvv", status_code=status.HTTP_200_OK)
async def create_cvv(
    pdf_file: UploadFile = File(...),
    description: str = Form(...)
):
    if not pdf_file or not pdf_file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum arquivo foi enviado"
        )
        
    if not pdf_file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O arquivo deve ser um PDF"
        )
    
    try:
        try:
            file_content = await pdf_file.read()
            if not file_content:
                raise ValueError("O arquivo PDF está vazio")
        except Exception as e:
            raise ValueError(f"Erro ao ler o arquivo: {str(e)}")
        
        if len(file_content) > 10 * 1024 * 1024:  
            raise ValueError("O arquivo é muito grande. O tamanho máximo permitido é 10MB.")
        
        try:
            conteudo_bruto_ia = gerar_conteudo_otimizado(file_content, description)
            if not conteudo_bruto_ia or not str(conteudo_bruto_ia).strip():
                raise ValueError("Não foi possível processar o conteúdo do currículo")
                
            dados_estruturados = parse_resposta_ia(conteudo_bruto_ia)
            
            if not dados_estruturados or not isinstance(dados_estruturados, dict):
                raise ValueError("Falha ao processar a estrutura do currículo")
                
            pdf_buffer = criar_pdf_estilizado_cv(dados_estruturados)
            
            if not pdf_buffer or pdf_buffer.getbuffer().nbytes == 0:
                raise ValueError("Falha ao gerar o PDF")
                
        except Exception as e:
            print(f"Erro ao processar o currículo: {e}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Erro ao processar o currículo: {str(e)}"
            )

        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=CV_Otimizado_{pdf_file.filename}",
                "Content-Length": str(pdf_buffer.getbuffer().nbytes)
            }
        )

    except HTTPException:
        raise
        
    except ValueError as ve:
        print(f"Erro de validação em /create-cvv: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
        
    except Exception as e:
        print(f"Erro inesperado em /create-cvv: {e}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um erro inesperado ao processar sua solicitação. Por favor, tente novamente mais tarde."
        )

