# Estágio 1: Base de Python estável
FROM python:3.11-slim

USER root

# Instalar dependências de sistema e Node.js (necessário para rodar o n8n)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g n8n@2.7.5 \
    && rm -rf /var/lib/apt/lists/*

# Instalar bibliotecas de dados para o MatchAI
RUN pip install --no-cache-dir pandas boto3 awscli --break-system-packages

# Configurar o script gerador
WORKDIR /opt/pharmacy
COPY generate_pharmacy.py .
RUN chmod +x generate_pharmacy.py

# Criar pastas necessárias para o n8n
RUN mkdir -p /root/.n8n /root/data

# Expor a porta do n8n
EXPOSE 5678

# Comando de inicialização
CMD ["n8n", "start"]
