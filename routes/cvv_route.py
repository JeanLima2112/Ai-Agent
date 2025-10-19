import os
import re
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
    temperature=0.5,
    api_key=os.getenv("GOOGLE_API_KEY"),
)

PROMPT_IA = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Você é um redator de currículos de elite, especialista em marketing pessoal e otimização para ATS. Sua missão é transformar o currículo fornecido em um documento de marketing de alto impacto, totalmente otimizado para sistemas de rastreamento de candidatos (ATS) que utilizam NLP e análise vetorial semântica.\n\n"
            "REGRAS DE TRANSFORMAÇÃO:\n"
            "1.  **Reenquadramento para Impacto**: Não liste responsabilidades, transforme-as em conquistas. Cada item de experiência deve responder à pergunta: 'Que valor ou resultado positivo eu gerei para a empresa?'.\n"
            "2.  **Quantificação Agressiva**: Sempre que possível, adicione métricas, percentuais, valores ou prazos. Caso não existam, inferir impactos com base na prática profissional.\n"
            "3.  **Linguagem de Liderança e Inovação**: Use verbos fortes e proativos como Orquestrei, Pioneirei, Otimizei, Escalei, Implementei, em vez de termos passivos.\n"
            "4.  **Alinhamento Estratégico com a Vaga**: Analise a vaga e identifique as dores e objetivos da empresa. Reescreva o currículo de modo que o candidato apareça como a solução direta para esses desafios.\n"
            "5.  **Comunicação Clara e Profissional**:\n"
            "    - Não use placeholders, colchetes ou textos pendentes.\n"
            "    - Não mencione ausência de dados.\n"
            "    - O tom deve ser profissional, assertivo e confiante.\n"
            "6.  **Alinhamento com a Vaga e Prevenção de Corte ATS**:\n"
            "    - Todas as exigências, palavras-chave, tecnologias, ferramentas e competências mencionadas na descrição da vaga **devem constar no currículo final**.\n"
            "    - Nenhuma palavra presente na descrição da vaga pode estar ausente. Se necessário, encaixe-a naturalmente na seção mais coerente.\n"
            "    - Isso previne cortes automáticos em sistemas ATS que fazem correspondência semântica.\n\n"
            "REGRAS DE NLP E ESPAÇO VETORIAL:\n"
            "- Os sistemas ATS modernos utilizam embeddings e análise vetorial semântica para medir a similaridade entre o texto do currículo e a descrição da vaga.\n"
            "- Portanto, além de repetir as palavras exatas da vaga, **utilize sinônimos, termos relacionados e palavras próximas no mesmo espaço vetorial**.\n"
            "- Exemplo: se a vaga pede 'desenvolvimento backend', inclua termos semanticamente próximos como 'API REST', 'integrações', 'arquitetura de servidor' e 'microsserviços'.\n"
            "- Garanta que o texto contenha alta densidade de palavras semanticamente correlatas à vaga, mas de forma natural e fluente.\n"
            "- Use variações morfológicas e léxicas das palavras-chave para aumentar o score semântico (ex: 'analisar', 'análise', 'analítico').\n\n"
            "REGRAS DE DENSIDADE E REPETIÇÃO:\n"
            "- Palavras-chave da vaga devem aparecer entre 2 e 3 vezes no texto total.\n"
            "- O cargo principal deve aparecer 2 vezes.\n"
            "- Cada tecnologia ou exigência técnica deve aparecer pelo menos 2 vezes, de forma contextual.\n"
            "- No resumo profissional, as palavras-chave devem constar 2 a 3 vezes.\n"
            "- Em competências e experiência, priorize repetições sutis e orgânicas.\n"
            "- Evite repetição mecânica (keyword stuffing). Prefira paráfrases e variações sintáticas.\n\n"
            "**METADADOS OBRIGATÓRIOS (insira esta seção no início da resposta, antes de tudo):**\n"
            "```\n"
            "METADADOS:\n"
            "TITULO: [Cargo Principal ou Desejado, extraído da descrição da vaga]\n"
            "AUTOR: [Nome do Candidato]\n"
            "PALAVRAS_CHAVE: [Extraia até 10 palavras-chave da DESCRIÇÃO DA VAGA, incluindo tecnologias, linguagens de programação, frameworks, ferramentas e bibliotecas específicas. Exemplo: Python, Django, PostgreSQL, Docker, AWS, React, Node.js, TensorFlow, Kubernetes, Git]\n"
            "DESCRICAO: [Resumo conciso da vaga, destacando os principais requisitos e responsabilidades, incluindo tecnologias.]\n"
            "CATEGORIA: currículo\n"
            "```\n\n"
            "**ESTRUTURA DE SAÍDA OBRIGATÓRIA (após os metadados, use EXATAMENTE este formato):**\n\n"
            "NOME: [Nome Completo do Candidato]\n\n"
            "CARGO: [Cargo Principal ou Desejado]\n\n"
            "RESUMO: [Parágrafo único e conciso do resumo profissional, alinhado com a vaga e otimizando repetição semântica.]\n\n"
            "EXPERIENCIA:\n"
            "- [Cargo] | [Empresa] | [Período]\n"
            "  - [Descrição da primeira conquista ou responsabilidade com termos da vaga e correlatos semânticos]\n"
            "  - [Descrição da segunda conquista, integrando palavras próximas no espaço vetorial]\n\n"
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
        ("user", "Extraia e reescreva o currículo a seguir, seguindo a estrutura definida. \n"
         "Analise cuidadosamente a descrição da vaga para extrair os metadados solicitados e alinhe o currículo com as necessidades da vaga.\n\n"
         "CURRÍCULO ORIGINAL:\n{context}\n\nVAGA DESCRITA:\n{input}"),
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


    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_content)
        tmp_path = tmp.name
    
    try:
        doc = fitz.open(tmp_path)
        if not doc:
            return "Curriculo"
            
        first_page = doc[0]
        text = first_page.get_text("text")
        
        if text:
            first_line = next((line.strip() for line in text.split('\n') if line.strip()), "")
            clean_name = ' '.join(first_line.split())
            if clean_name and len(clean_name) > 2:
                return clean_name
        
        return "Curriculo"
    except Exception as e:
        print(f"Erro ao extrair nome do PDF: {e}")
        return "Curriculo"
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
        "CONTATO": [],
        "METADADOS": {
            "TITULO": "",
            "AUTOR": "",
            "PALAVRAS_CHAVE": "",
            "DESCRICAO": "",
            "CATEGORIA": "currículo"
        }
    }
    
    if not texto_ia or not isinstance(texto_ia, str) or not texto_ia.strip():
        print("ERRO: Texto da IA vazio ou inválido")
        return data
    
    current_section = None
    
    try:
        for line in texto_ia.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
            
            if line.startswith("```") and "METADADOS" in line.upper():
                print("\n=== INÍCIO DO BLOCO DE METADADOS ===")
                current_section = "METADADOS"
                continue
                
            if current_section == "METADADOS":
                if line.startswith("```"):
                    print("=== FIM DO BLOCO DE METADADOS ===\n")
                    print("Metadados extraídos:", data["METADADOS"])
                    current_section = None
                    continue
                    
                if ":" in line:
                    key_part = line.split(":", 1)[0].strip().upper()
                    value = line.split(":", 1)[1].strip()
                    print(f"Processando metadado: {key_part} = {value}")
                    if key_part in data["METADADOS"]:
                        data["METADADOS"][key_part] = value
                        print(f"Metadado '{key_part}' definido como: {value}")
                    else:
                        print(f"AVISO: Chave de metadado desconhecida: {key_part}")
                continue
                        
            if ":" in line and current_section != "METADADOS":
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
        print(f"ERRO CRÍTICO ao processar resposta da IA: {e}")
        import traceback
        traceback.print_exc()
        print("Estado parcial dos dados:", data)
        return data

def criar_pdf_estilizado_cv(dados_cv: Dict[str, Any], descricao_vaga: str = "") -> BytesIO:
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
            
            line_width = 1.5
            line_length = 500
            
            page.draw_line(
                (margem, y_pos - 5),
                (margem + line_length, y_pos - 5),
                color=cor_titulo,
                width=line_width
            )
            y_pos += 15
        
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
        
        if dados_cv.get("EXPERIENCIA"):
            print(f"\n--- ADICIONANDO EXPERIÊNCIA PROFISSIONAL ---")
            
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
                
                if isinstance(exp, str):
                    exp = {"titulo": exp, "detalhes": []}
                elif not isinstance(exp, dict):
                    print(f"  Experiência {idx}: Formato não suportado")
                    continue
                
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
                
                if exp.get("detalhes") and isinstance(exp["detalhes"], list):
                    print(f"  Número de detalhes: {len(exp['detalhes'])}")
                    for detalhe in exp["detalhes"]:
                        if not detalhe:
                            continue
                            
                        print(f"  Processando detalhe: {detalhe[:100]}...")
                        
                        texto = str(detalhe).strip()
                        linhas = []
                        while len(texto) > 150:
                            espaco = texto[:150].rfind(' ')
                            if espaco == -1:
                                espaco = 150
                            linhas.append(texto[:espaco])
                            texto = texto[espaco:].strip()
                        if texto:
                            linhas.append(texto)
                        
                        for i, linha in enumerate(linhas):
                            prefixo = "• " if i == 0 else "  "
                            y_pos = adicionar_texto(
                                margem + 20, y_pos,
                                f"{prefixo}{linha}",
                                fonte_normal, 10, cor_texto
                            )
                            y_pos += 5  
                        
                        y_pos += 2  
                
                y_pos += 5  
        
        if dados_cv.get("FORMACAO"):
            print(f"\n--- ADICIONANDO FORMAÇÃO ACADÊMICA ---")
            
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
                
                if isinstance(form, str):
                    y_pos = adicionar_texto(
                        margem, y_pos,
                        f"• {form}",
                        fonte_normal, 10, cor_texto
                    )
                    y_pos += 3
                    continue
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
        
        print("\n=== GERANDO PDF FINAL ===")
        metadata = doc.metadata
        
        if dados_cv.get("METADADOS"):
            metadados = dados_cv["METADADOS"]
            print(f"\n=== METADADOS EXTRAÍDOS ===")
            print(f"Título: {metadados.get('TITULO')}")
            print(f"Autor: {metadados.get('AUTOR')}")
            print(f"Descrição: {metadados.get('DESCRICAO')}")
            print(f"Palavras-chave: {metadados.get('PALAVRAS_CHAVE')}")
            
            if metadados.get("TITULO"):
                metadata["title"] = str(metadados["TITULO"])
                print(f"Definindo título do PDF: {metadata['title']}")
            elif dados_cv.get("CARGO"):
                metadata["title"] = str(dados_cv["CARGO"])
                print(f"Usando cargo como título do PDF: {metadata['title']}")
            
            if metadados.get("AUTOR"):
                metadata["author"] = str(metadados["AUTOR"])
                print(f"Definindo autor do PDF: {metadata['author']}")
            elif dados_cv.get("NOME"):
                metadata["author"] = str(dados_cv["NOME"])
                print(f"Usando nome como autor do PDF: {metadata['author']}")
            
            if metadados.get("DESCRICAO"):
                descricao = str(metadados["DESCRICAO"])
                frases = [f.strip() for f in descricao.split('.') if f.strip()]
                
                if len(frases) >= 2:
                    linha1 = frases[0][:200]
                    linha2 = frases[1][:200] if len(frases) > 1 else linha1
                else:
                    meio = len(descricao) // 2
                    linha1 = descricao[:meio].strip()
                    linha2 = descricao[meio:].strip()
                
                metadata["subject"] = f"{linha1}\n{linha2}"
                print(f"Assunto formatado (2 linhas):\n{metadata['subject']}")
                
            elif dados_cv.get("RESUMO"):
                resumo = str(dados_cv["RESUMO"])
                meio = len(resumo) // 2
                linha1 = resumo[:meio].strip()
                linha2 = resumo[meio:].strip()
                metadata["subject"] = f"{linha1}\n{linha2}"
                print(f"Usando resumo como assunto (2 linhas):\n{metadata['subject']}")
            
            if metadados.get("PALAVRAS_CHAVE"):
                palavras_chave = metadados['PALAVRAS_CHAVE']
                if isinstance(palavras_chave, str):
                    palavras = [p.strip() for p in palavras_chave.split(',') if p.strip()]
                else:
                    palavras = [str(p).strip() for p in palavras_chave]
                
                palavras = [p for p in palavras if len(p) > 3][:10]  # Limita a 10 palavras-chave
                
                if palavras:
                    metadata["keywords"] = ", ".join(["currículo"] + palavras)
                    print(f"Palavras-chave extraídas: {metadata['keywords']}")
                
            elif dados_cv.get("RESUMO"):
                resumo = str(dados_cv["RESUMO"])
                palavras = [p for p in re.findall(r'\b\w{4,}\b', resumo.lower()) 
                          if p not in ['sobre', 'para', 'como', 'mais', 'muito', 'sobre', 'sobre', 'sobre']][:10]
                if palavras:
                    metadata["keywords"] = ", ".join(["currículo"] + palavras)
                    print(f"Palavras-chave extraídas do resumo: {metadata['keywords']}")
            
            print("=== FIM DOS METADADOS EXTRAÍDOS ===\n")
        
        doc.set_metadata(metadata)
        
        pdf_buffer = BytesIO()
        doc.save(pdf_buffer)
        pdf_buffer.seek(0)
        
        print(f"Tamanho do PDF gerado: {len(pdf_buffer.getvalue())} bytes")
        print(f"Metadados do PDF: {metadata}")
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
    print("\n=== INÍCIO DO PROCESSAMENTO DO CV ===")
    print(f"Arquivo recebido: {pdf_file.filename}")
    print(f"Descrição da vaga: {description}")
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
            print("\nLendo conteúdo do arquivo PDF...")
            file_content = await pdf_file.read()
            if not file_content:
                print("ERRO: O arquivo PDF está vazio")
                raise ValueError("O arquivo PDF está vazio")
        except Exception as e:
            raise ValueError(f"Erro ao ler o arquivo: {str(e)}")
        
        if len(file_content) > 10 * 1024 * 1024:  
            raise ValueError("O arquivo é muito grande. O tamanho máximo permitido é 10MB.")
        
        try:
            print("\nChamando gerar_conteudo_otimizado...")
            conteudo_bruto_ia = gerar_conteudo_otimizado(file_content, description)
            if not conteudo_bruto_ia or not str(conteudo_bruto_ia).strip():
                print("ERRO: Não foi possível processar o conteúdo do currículo - retorno vazio da IA")
                raise ValueError("Não foi possível processar o conteúdo do currículo")
            
            print("\nConteúdo bruto da IA (primeiros 500 caracteres):")
            print(str(conteudo_bruto_ia)[:500] + ("..." if len(str(conteudo_bruto_ia)) > 500 else ""))
                
            print("\nIniciando análise da resposta da IA...")
            dados_estruturados = parse_resposta_ia(conteudo_bruto_ia)
            
            if not dados_estruturados or not isinstance(dados_estruturados, dict):
                print("ERRO: Falha ao processar a estrutura do currículo - dados_estruturados inválido")
                print(f"Tipo de dados_estruturados: {type(dados_estruturados)}")
                print(f"Conteúdo: {dados_estruturados}")
                raise ValueError("Falha ao processar a estrutura do currículo")
                
            print("\nDados estruturados processados com sucesso")
                
            print("\nCriando PDF estilizado...")
            print(f"Dados sendo passados para criar_pdf_estilizado_cv: {list(dados_estruturados.keys())}")
            print(f"Metadados disponíveis: {dados_estruturados.get('METADADOS', 'Nenhum metadado encontrado')}")
            
            pdf_buffer = criar_pdf_estilizado_cv(dados_estruturados, description)
            
            if not pdf_buffer or pdf_buffer.getbuffer().nbytes == 0:
                print("ERRO: Falha ao gerar o PDF - buffer vazio ou inválido")
                raise ValueError("Falha ao gerar o PDF")
                
            print(f"PDF gerado com sucesso! Tamanho: {pdf_buffer.getbuffer().nbytes} bytes")
                
        except Exception as e:
            print(f"Erro ao processar o currículo: {e}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Erro ao processar o currículo: {str(e)}"
            )

        nome_candidato = dados_estruturados.get("NOME", "Curriculo").strip()
        
        nome_arquivo = f"{nome_candidato}-Curriculo.pdf"
        nome_arquivo = "".join(c if c.isalnum() or c in ('-', '_', '.', ' ') else '_' for c in nome_arquivo)
        nome_arquivo = nome_arquivo.replace(" ", "_")
        if not nome_arquivo.lower().endswith('.pdf'):
            nome_arquivo += '.pdf'
        
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=\"{nome_arquivo}\"",
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

