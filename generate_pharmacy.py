import pandas as pd
import boto3
import os
import gc  # Import para gerenciamento de memória
from io import StringIO
from datetime import datetime

def main():
    # 1. Configurações de Ambiente e Conexão
    endpoint = os.getenv('SUPABASE_S3_ENDPOINT')
    access_key = os.getenv('AWS_ACCESS_KEY_ID')
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    region = os.getenv('AWS_DEFAULT_REGION', 'sa-east-1')
    bucket = "b2list"
    
    print(f"[{datetime.now()}] Iniciando consolidação MatchAI...")
    
    s3_client = boto3.client(
        's3', 
        endpoint_url=endpoint, 
        aws_access_key_id=access_key, 
        aws_secret_access_key=secret_key, 
        region_name=region
    )
    
    def get_df(key):
        """Baixa do S3 e normaliza, otimizando tipos de dados para economizar RAM"""
        print(f"  -> Baixando {key}...")
        obj = s3_client.get_object(Bucket=bucket, Key=key)
        # Otimização: low_memory=False ajuda na performance de leitura
        df = pd.read_csv(obj['Body'], sep=';', low_memory=False)
        df.columns = df.columns.str.strip().str.upper()
        return df
    
    try:
        # 2. Carregamento das Fontes (Consumo de RAM inicia aqui)
        df_maestro = get_df('Maestro.csv')
        df_associados = get_df('Associados.csv')
        df_terceros = get_df('Terceros.csv')

        # 3. Joins
        pharmacy = df_maestro.merge(df_associados, on='ID', how='left', suffixes=('', '_ASSOC'))
        pharmacy = pharmacy.merge(df_terceros, on='ID', how='left', suffixes=('', '_TERC'))
        
        # Limpeza imediata das tabelas de origem após o Merge
        del df_maestro, df_associados, df_terceros
        gc.collect()

        # 4. Mapeamento de Campos
        pharmacy['trade_name'] = pharmacy['NOME_ASSOC'].fillna(pharmacy['NOME_TERC'])
        pharmacy['corporate_name'] = pharmacy['NOME_FANTASIA']
        pharmacy['nit'] = pharmacy['NIT']
        pharmacy['code_pharmacy'] = pharmacy['ID']
        
        col_lat_assoc = 'LATITUDE_ASSOC' if 'LATITUDE_ASSOC' in pharmacy.columns else 'LATITUDE'
        col_lon_assoc = 'LONGITUDE_ASSOC' if 'LONGITUDE_ASSOC' in pharmacy.columns else 'LONGITUDE'
        
        pharmacy['lat'] = pharmacy[col_lat_assoc].fillna(pharmacy['LATITUDE_TERC'])
        pharmacy['lon'] = pharmacy[col_lon_assoc].fillna(pharmacy['LONGITUDE_TERC'])
        pharmacy['category'] = pharmacy['NOME_ASSOC'].isna().map({True: 'TERCERO', False: 'ASSOCIADO'})
        
        obs_col = 'OBSERVACAO_ASSOC' if 'OBSERVACAO_ASSOC' in pharmacy.columns else 'OBSERVACAO'
        observacao = pharmacy[obs_col].fillna(pharmacy['OBSERVACAO_TERC'])
        termos = r'Em dia|Ativo|Cadastro Ativo|Verificado|Vigente'
        pharmacy['enabled'] = observacao.str.contains(termos, case=False, na=False, regex=True)
        
        # 5. Seleção Final
        final = pharmacy[[
            'code_pharmacy', 'nit', 'trade_name', 'corporate_name', 
            'lat', 'lon', 'category', 'enabled'
        ]]
        
        # 6. Exportação (Separador ; e Decimal ,)
        csv_buffer = StringIO()
        final.to_csv(csv_buffer, index=False, sep=';', decimal=',')
        
        # 7. Upload para S3
        s3_client.put_object(
            Bucket=bucket, 
            Key='pharmacy.csv', 
            Body=csv_buffer.getvalue(), 
            ContentType='text/csv'
        )
        
        print(f"[{datetime.now()}] Sucesso: pharmacy.csv gerado com {len(final)} linhas.")

        # --- GESTÃO AGRESSIVA DE MEMÓRIA ---
        del pharmacy
        del final
        gc.collect()  # Força a liberação da RAM de volta para o SO
        # -----------------------------------

        return {'status': 'success'}

    except Exception as e:
        print(f"!!! ERRO FATAL: {str(e)}")
        # Garante limpeza mesmo em caso de erro
        gc.collect()
        raise e

if __name__ == '__main__':
    main()
