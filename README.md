# ---

**MatchAI: Pipeline de Consolidação de Dados de Farmácias**

Este repositório contém a solução completa para o pipeline de dados automatizado do desafio técnico **Head de Dados**. O ecossistema integra extração SFTP, processamento em Python, armazenamento S3 e sincronização incremental com PostgreSQL.

## **🚀 Arquitetura da Solução**

O pipeline é composto por três workflows principais orquestrados no **n8n**, utilizando uma base de dados **Supabase** para persistência e **Python** para transformações complexas:

1. **B2list S3 Files Flow:** Gerencia a ingestão de arquivos brutos do SFTP para o S3 e dispara a geração da base consolidada.

2. **First Sync Postgres:** Realiza a carga inicial (bulk load) após o truncate da tabela.

3. **Incremental Sync Postgres:** Mantém a base atualizada realizando operações de INSERT, UPDATE e SOFT DELETE em lote.

## ---

**🛠️ Configuração de Credenciais (n8n)**

Para o funcionamento correto dos fluxos, as seguintes credenciais devem ser configuradas no painel do n8n:

### **1\. Supabase "S3 compatible" Storage**

Utilizada para interação com o bucket de arquivos CSV.

* **Endpoint:** https://\[instancia\].storage.supabase.co/storage/v1/s3

* **Region:** sa-east-1 (ou conforme seu projeto)

* **S3 Force Path Style:** **True** (Obrigatório para compatibilidade com Supabase)  
  \+2

### **2\. Supabase API (PostgREST)**

Utilizada para chamadas RPC e operações diretas na tabela via HTTP Request.

* **URL:** https://\[instancia\].supabase.co

* **API Key:** Sua service\_role key para bypass de RLS.

### **3\. B2list SFTP Account**

Utilizada para coleta dos arquivos Maestro.csv, Associados.csv e Terceros.csv.

* **Host/Port:** Conforme definido no seu servidor de origem.

## ---

**📋 Procedimento de Instalação**

### **1\. Preparação do Ambiente Local e Cloud**

* **Arquivos .env:** Renomeie .env.example para .env e preencha todas as variáveis, especialmente as chaves de criptografia e credenciais de banco.

* **Estrutura de Pastas:** Mantenha as pastas /n8n\_data, /aws\_config e /root/data conforme a estrutura do repositório para garantir o mapeamento correto dos volumes Docker.  
  \+2

### **2\. Configuração de Banco de Dados (Supabase)**

1. **Conexão:** Utilize obrigatoriamente o **Transaction Pooler** (Porta 6543) para evitar exaustão de conexões no ambiente serverless.

2. **Scripts SQL:** Execute o conteúdo de sql/postgres\_SQL\_setup.sql no SQL Editor do Supabase para criar as tabelas, índices e as funções RPC update\_pharmacy\_batch e truncate\_table\_by\_name.

### **3\. Deploy no Render**

1. Crie um novo **Web Service** apontando para este repositório.  
2. Adicione todas as linhas do seu .env na seção **Environment Variables** do Render.  
   \+1

3. Certifique-se de que a variável PORT está como 5678.

4. Caso utilize outro serviço de hospedagem, lembre-se de atualizar a WEBHOOK\_URL.

## ---

**🔄 Fluxos do n8n**

Os arquivos JSON para importação estão localizados na pasta n8n\_data na raiz do projeto.

### **Ingestão e Geração (S3 Flow)**

Este fluxo automatiza a coleta do SFTP e a execução do script Python generate\_pharmacy.py.

### **Sincronização Incremental**

Lógica avançada para identificar novos registros ou alterações, disparando a atualização em lotes de 500 itens para performance.

## ---

**⚙️ Notas Técnicas**

* **Python:** O script generate\_pharmacy.py substitui automaticamente o arquivo no destino e utiliza ; como separador para manter compatibilidade com os sistemas legados.

* **Bash/S3:** O workflow utiliza o AWS CLI v1 interno do container para transferir arquivos diretamente do sistema de arquivos para o S3, otimizando o uso de memória.

---

**Desenvolvido para o desafio técnico Head de Dados \- Gilberto Ciola \-  2026\.**