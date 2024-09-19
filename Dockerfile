# Etapa 1: Construir o projeto Angular
FROM node:18 AS builder

WORKDIR /app-build

# Copiar os arquivos necessários para o Angular
COPY frontend/package*.json ./

# Instalar as dependências do Angular
RUN npm install -g @angular/cli@17.0.3 && npm install

RUN npm install jwt-decode





# Copiar o restante do código do projeto Angular
COPY frontend/ ./

# Compilar o projeto Angular
RUN ng build --configuration production

# Etapa 2: Configurar a aplicação Flask
FROM python:3.8-slim

WORKDIR /backend

# Copiar o arquivo requirements.txt
COPY backend/requirements.txt /backend

# Instalar as dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar os arquivos do projeto Flask
COPY backend/ /backend/


# Expor a porta da aplicação
EXPOSE 5000

# Comando para iniciar a aplicação
CMD ["python", "./src/app.py"]
