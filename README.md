# **MatchAI: Pipeline de Consolidação de Dados de Farmácias**

Este repositório contém a solução completa para o pipeline de dados automatizado do desafio técnico **Head de Dados**. O sistema integra extração SFTP, processamento em Python, armazenamento S3 e sincronização incremental com PostgreSQL.

## **🚀 Arquitetura da Solução**

O pipeline é orquestrado no **n8n** (hospedado no Render) e utiliza **Python 3.11** para transformações complexas. A persistência é realizada em uma instância **Supabase**, utilizando o motor PostgreSQL para dados relacionais e o Storage compatível com S3 para arquivos.

\+2

## ---

**🛠️ Configuração do Ambiente Supabase**

Antes de iniciar o pipeline, é necessário preparar a infraestrutura no painel do Supabase:

1. **Criação do Bucket:** Acesse a aba **Storage** e crie um novo bucket chamado exatamente b2list.  
   \+1

2. **Configuração S3:** \* Acesse as configurações de **S3 Storage** no painel do Supabase.  
   \+1

   * Gere uma **Access Key** e uma **Secret Key** válidas.

   * Salve estes valores no seu arquivo .env ou no painel do Render.

3. **Massa de Teste (Opcional):** \* Para demonstrar a funcionalidade de **Soft Delete** do pipeline, insira manualmente um arquivo chamado pharmacy-excluded.csv no bucket.  
   * Dica: Utilize uma cópia do pharmacy.csv removendo 5 linhas aleatórias; o sistema detectará a ausência e desativará os registros no banco.

## ---

**📋 Configuração do n8n**

### **1\. Variáveis Globais e Data Table do N8N**

Se você estiver migrando para uma **nova conta do Supabase**, é necessário atualizar a referência global:

* Acesse o componente **Data Table** no n8n chamado SUPABASE\_URL.  
  \+1

* Na coluna URL, substitua o valor existente pela nova URL do projeto (ex: https://xxxxxxxxxxx.supabase.co).  
  \+1

### **2\. Credenciais Críticas no N8N**

Configure as seguintes credenciais no painel do n8n:

* **Supabase "S3 compatible" Storage:** \* **Endpoint:** Sua URL do S3 Storage.

  * **S3 Force Path Style:** **True** (Essencial para o funcionamento das chamadas).

* **Supabase Account (API):** Utilize a service\_role key para permitir operações de RPC e Truncate.  
* **B2List SFTP account:** Insira o host, a porta, o usuário e a senha conforme adicionado no .env.

## ---

**⚙️ Procedimento de Instalação (Render e Supabase)**

1. **Variáveis de Ambiente:** Renomeie .env.example para .env e preencha as chaves. Copie estes valores para o painel de **Environment** do Render.

2. **Scripts SQL:** Execute o conteúdo de /sql/postgres\_SQL\_setup.sql no SQL Editor do Supabase para criar a tabela pharmacy e as funções RPC de lote.

3. **Segurança:** Certifique-se de que N8N\_BLOCK\_SVC\_COMMAND\_EXECUTION=false e N8N\_DISABLE\_PRODUCTION\_MAIN\_PROCESS\_CONTROL=true estão configurados para evitar travamentos na interface.

## ---

**🔄 Fluxos a Adicionar**

Os JSONs do N8N para importação estão na pasta /n8n\_data:

* **B2list S3 Files Flow:** Ingestão SFTP \-\> S3 \-\> Geração Python.  
* **First Sync Postgres:** Carga inicial pós-truncate.  
* **Incremental Sync Postgres:** Sync de INSERT/UPDATE/DELETE em lote.

## ---

**Desenvolvido para o desafio técnico Head de Dados \- 2026\.**
