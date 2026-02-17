# ESTÁGIO 1: Builder para Ferramentas de Infra (AWS CLI e Docker CLI)
FROM python:3.11-alpine AS infra-builder
RUN apk add --no-cache curl gcc musl-dev python3-dev libffi-dev docker-cli docker-cli-compose
RUN pip install --no-cache-dir awscli

# ESTÁGIO 2: Preparação do Gerador de Dados (Pharmacy)
FROM python:3.11-slim AS pharmacy-generator
WORKDIR /app
RUN pip install --no-cache-dir pandas boto3
COPY generate_pharmacy.py .
RUN chmod +x generate_pharmacy.py

# ESTÁGIO 3: Imagem Final n8n Customizada
FROM docker.n8n.io/n8nio/n8n:2.7.5
USER root

# Copiar ferramentas do Estágio 1 (Infra)
COPY --from=infra-builder /usr/local/bin/aws /usr/local/bin/aws
COPY --from=infra-builder /usr/bin/docker /usr/bin/docker
COPY --from=infra-builder /usr/bin/docker-compose /usr/bin/docker-compose

# Copiar o ambiente Python e dependências do gerador
# Nota: Mantemos o gerador isolado na pasta /opt/pharmacy para o n8n disparar
mkdir -p /opt/pharmacy
COPY --from=pharmacy-generator /app /opt/pharmacy
COPY --from=pharmacy-generator /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Configuração de diretórios e permissões
RUN mkdir -p /root/.n8n /root/.aws /root/workflows /root/data && \
    chmod -R 755 /root/data

ENV PATH="/usr/local/bin:$PATH"
USER root