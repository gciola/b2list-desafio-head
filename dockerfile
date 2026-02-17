# ESTÁGIO 1: Builder para coletar o AWS CLI (evita levar compiladores para a imagem final)
FROM python:3.11-slim AS builder
RUN pip install --no-cache-dir awscli

# ESTÁGIO 2: Preparação do Gerador (Pandas + Boto3)
FROM python:3.11-slim AS pharmacy-env
WORKDIR /app
RUN pip install --no-cache-dir pandas boto3
COPY generate_pharmacy.py .

# ESTÁGIO 3: Imagem Final n8n (Onde tudo se une)
FROM docker.n8n.io/n8nio/n8n:2.7.5
USER root

# Reinstalando pacotes de infra que você sinalizou, mas sem os compiladores (dev-libs)
# O curl e docker-cli são leves e essenciais
RUN apk add --no-cache curl docker-cli

# Trazendo o AWS CLI do estágio 1 (já instalado, sem precisar de gcc/musl aqui)
COPY --from=builder /usr/local/bin/aws /usr/local/bin/aws
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Trazendo o Gerador de Dados e o Pandas
COPY --from=pharmacy-env /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=pharmacy-env /app/generate_pharmacy.py /opt/generate_pharmacy.py

# Configurações de ambiente para o n8n encontrar o Python e as Libs
ENV PYTHONPATH=/usr/local/lib/python3.11/site-packages
ENV PATH="/usr/local/bin:$PATH"

# Criando pastas de volume para evitar erros de permissão, mesmo sem disco persistente
RUN mkdir -p /root/.n8n /root/.aws /root/data && chmod -R 777 /root/data

USER root
