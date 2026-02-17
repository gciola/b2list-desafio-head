# Usando a imagem oficial do n8n como base
FROM docker.n8n.io/n8nio/n8n:2.7.5

USER root

# Tenta instalar usando APK (Alpine) ou APT (Debian) dinamicamente
RUN if [ -f /sbin/apk ]; then \
        apk add --no-cache curl python3 py3-pip docker-cli; \
    else \
        apt-get update && apt-get install -y --no-install-recommends curl python3 python3-pip docker.io && rm -rf /var/lib/apt/lists/*; \
    fi 

# Instalar bibliotecas Python necessárias para o MatchAI
# Usamos --break-system-packages para permitir instalação em ambientes gerenciados
RUN pip install --no-cache-dir pandas boto3 --break-system-packages 

# Copiar o script gerador diretamente para a imagem
COPY generate_pharmacy.py /opt/generate_pharmacy.py 
RUN chmod +x /opt/generate_pharmacy.py [cite: 6]

# Garantir que o Python e AWS CLI (via pip) estejam no PATH
RUN pip install --no-cache-dir awscli --break-system-packages 

# Variáveis de ambiente para persistência no Supabase (configurar no Render)
ENV N8N_PORT=5678
ENV PYTHONUNBUFFERED=1

USER root
