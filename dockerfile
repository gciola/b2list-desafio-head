# ESTÁGIO 1: Builder para coletar o AWS CLI (evita levar compiladores para a imagem final)
FROM python:3.11-slim AS builder
RUN pip install --no-cache-dir awscli

# ESTÁGIO 2: Preparação do Gerador (Pandas + Boto3)
FROM python:3.11-slim AS pharmacy-env
WORKDIR /app
RUN pip install --no-cache-dir pandas boto3
COPY generate_pharmacy.py .

# ESTÁGIO 3: Imagem Final n8n (Debian-based)
FROM docker.n8n.io/n8nio/n8n:2.7.5
USER root

# Ajuste para Debian: usa-se apt-get em vez de apk
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Trazendo o AWS CLI e Gerador conforme estágios anteriores
COPY --from=builder /usr/local/bin/aws /usr/local/bin/aws
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=pharmacy-env /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=pharmacy-env /app/generate_pharmacy.py /opt/generate_pharmacy.py

ENV PYTHONPATH=/usr/local/lib/python3.11/site-packages
ENV PATH="/usr/local/bin:$PATH"

RUN mkdir -p /root/.n8n /root/.aws /root/data && chmod -R 777 /root/data
USER root
