# WorkReadyAI 🚀

<div align="center">

![Logo WorkReadyAI](public/logos/logo.png)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Enabled-blue.svg)](https://www.docker.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Ready-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-Powered-blue.svg)](https://reactjs.org/)

</div>

## 📋 Sobre o Projeto

WorkReadyAI é uma aplicação web inovadora que otimiza currículos para sistemas de rastreamento de candidatos (ATS). Utilizando a API da Google, nossa ferramenta analisa currículos e descrições de vagas, reescrevendo-os estrategicamente para maximizar as chances de aprovação automática.

## ✨ Funcionalidades

- 📄 **Otimização de Currículo**
  - Upload de PDF
  - Análise de descrição de vaga
  - Geração de versão otimizada
- 🎯 **Interface Intuitiva**

  - Design moderno e responsivo
  - Upload simplificado de arquivos
  - Interface amigável ao usuário

- ⚡ **Alta Performance**
  - Backend rápido com FastAPI
  - Frontend otimizado em React
  - Containerização com Docker

## 🛠️ Tecnologias

### Backend

- 🐍 Python 3.10
- ⚡ FastAPI
- 🚀 Uvicorn
- 🔗 LangChain
- 🤖 Google Generative AI
- 📑 PyMuPDF

### Frontend

- ⚛️ React
- 📦 Node.js 20
- ⚡ Vite
- 🔷 TypeScript
- 🎨 Tailwind CSS
- 🔄 Axios

## 📁 Estrutura do Projeto

Work_Ready-AI/  
├── backend/ # Código do backend em Python  
│ ├── app/ # Lógica principal da aplicação  
│ │ ├── routes/ # Endpoints da API  
│ │ ├── services/ # Serviços de processamento e integração com IA  
│ │ └── utils/ # Funções utilitárias  
│ ├── Dockerfile # Dockerfile do backend  
│ └── requirements.txt # Dependências do Python  
├── frontend/ # Código do frontend em React  
│ ├── src/ # Código fonte da aplicação  
│ ├── Dockerfile # Dockerfile do frontend  
│ └── package.json # Dependências do Node.js  
├── docker-compose.yml # Configuração dos containers  
├── .env.example # Exemplo de variáveis de ambiente  
└── Makefile # Comandos auxiliares

## Pré-requisitos

- Docker
- Docker Compose

## 🚀 Como Iniciar

### Pré-requisitos

- Docker
- Docker Compose

### Instalação

1. **Clone o Repositório**

   ```bash
   git clone https://github.com/JeanLima2112/Work_Ready-AI.git
   cd Work_Ready-AI
   ```

2. **Configure o Ambiente**

   - Crie um arquivo `.env` baseado no `.env.example`:

   ```env
   # API Keys
   GOOGLE_API_KEY=sua_google_api_key

   # URLs
   VITE_API_URL=http://localhost:8000

   # Configurações
   VITE_THEME="light"
   ```

3. **Inicie os Containers**

   ```bash
   docker-compose up -d --build
   ```

4. **Acesse a Aplicação**
   - Frontend: [http://localhost:5173](http://localhost:5173)
   - Backend: [http://localhost:8000](http://localhost:8000)

## 🛠️ Comandos Docker

```bash
# Iniciar serviços
docker-compose up -d

# Parar serviços
docker-compose down

# Visualizar logs
docker-compose logs -f
```

## 📝 Licença

Este projeto está licenciado sob a [Licença MIT](LICENSE).
