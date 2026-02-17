import pandas as pd
import boto3
import os
from io import StringIO
from datetime import datetime

def main():
    # 1. Configurações de Ambiente e Conexão 
    endpoint = os.getenv('SUPABASE_S3_ENDPOINT') [cite: 3]
    access_key = os.getenv('AWS_ACCESS_KEY_ID') [cite: 3]
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY') [cite: 3]
    region = os.getenv('AWS_DEFAULT_REGION', 'sa-east-1') [cite: 3]
    bucket = "b2list" [cite: 3]
    
    print(f"[{datetime.now()}] Iniciando consolidação MatchAI...")
    
    s3_client = boto3.client(
        's3', 
        endpoint_url=endpoint, 
        aws_access_key_id=access_key, 
        aws_secret_access_key=secret_key, 
        region_name=region
    )
    
    def get_df(key):
        """Baixa do S3 e normaliza cabeçalhos e separadores"""
        print(f"  -> Baixando {key}...")
        obj = s3_client.get_object(Bucket=bucket, Key=key) [cite: 3]
        # Seus arquivos usam ';' como separador 
        df = pd.read_csv(obj['Body'], sep=';') [cite: 3]
        # Normaliza colunas para evitar erros de case-sensitivity 
        df.columns = df.columns.str.strip().str.upper() [cite: 3]
        return df
    
    try:
        # 2. Carregamento das Fontes 
        df_maestro = get_df('Maestro.csv') [cite: 3]
        df_associados = get_df('Associados.csv') [cite: 3]
        df_terceros = get_df('Terceros.csv') [cite: 3]

        # 3. Joins Estratégicos (Maestro como Âncora) 
        # Primeiro merge com Associados 
        pharmacy = df_maestro.merge(df_associados, on='ID', how='left', suffixes=('', '_ASSOC')) [cite: 3]
        
        # Segundo merge com Terceros 
        pharmacy = pharmacy.merge(df_terceros, on='ID', how='left', suffixes=('', '_TERC')) [cite: 3]
        
        print("  -> Joins realizados. Iniciando mapeamento de campos...")

        # 4. Construção das Colunas Finais (Lógica de Precedência) 
        # Trade Name: Prioridade para Associado, depois Terceiro 
        pharmacy['trade_name'] = pharmacy['NOME_ASSOC'].fillna(pharmacy['NOME_TERC']) [cite: 3]
        
        # NIT e Razão Social vêm exclusivamente do Maestro 
        pharmacy['corporate_name'] = pharmacy['NOME_FANTASIA'] [cite: 3]
        pharmacy['nit'] = pharmacy['NIT'] [cite: 3]
        pharmacy['code_pharmacy'] = pharmacy['ID'] [cite: 3]
        
        # Coordenadas: Prioridade para Associado 
        col_lat_assoc = 'LATITUDE_ASSOC' if 'LATITUDE_ASSOC' in pharmacy.columns else 'LATITUDE' [cite: 3]
        col_lon_assoc = 'LONGITUDE_ASSOC' if 'LONGITUDE_ASSOC' in pharmacy.columns else 'LONGITUDE' [cite: 3]
        
        pharmacy['lat'] = pharmacy[col_lat_assoc].fillna(pharmacy['LATITUDE_TERC']) [cite: 3]
        pharmacy['lon'] = pharmacy[col_lon_assoc].fillna(pharmacy['LONGITUDE_TERC']) [cite: 3]
        
        # Categoria: Identificada pela origem do registro 
        pharmacy['category'] = pharmacy['NOME_ASSOC'].isna().map({True: 'TERCERO', False: 'ASSOCIADO'}) [cite: 3]
        
        # 5. Regra de Negócio: Enabled (Regex nos campos de Observação) 
        obs_col = 'OBSERVACAO_ASSOC' if 'OBSERVACAO_ASSOC' in pharmacy.columns else 'OBSERVACAO' [cite: 3]
        observacao = pharmacy[obs_col].fillna(pharmacy['OBSERVACAO_TERC']) [cite: 3]
        termos = r'Em dia|Ativo|Cadastro Ativo|Verificado|Vigente' [cite: 3]
        pharmacy['enabled'] = observacao.str.contains(termos, case=False, na=False, regex=True) [cite: 3]
        
        # 6. Seleção e Limpeza Final 
        final = pharmacy[[
            'code_pharmacy', 'nit', 'trade_name', 'corporate_name', 
            'lat', 'lon', 'category', 'enabled'
        ]] [cite: 3]
        
        # 7. Exportação e Upload para S3 
        csv_buffer = StringIO() [cite: 3]
        
        # AJUSTE #1: Separador de campos ';' e decimais ',' para paridade com origens
        final.to_csv(csv_buffer, index=False, sep=';', decimal=',')
        
        # AJUSTE #2: O método put_object substitui automaticamente o arquivo existente
        print(f"  -> Fazendo upload para s3://{bucket}/pharmacy.csv (Substituindo anterior)...")
        s3_client.put_object(
            Bucket=bucket, 
            Key='pharmacy.csv', 
            Body=csv_buffer.getvalue(), 
            ContentType='text/csv'
        )
        
        print(f"[{datetime.now()}] Sucesso: pharmacy.csv gerado com {len(final)} linhas.")
        return {'status': 'success', 'rows': len(final)}

    except Exception as e:
        print(f"!!! ERRO FATAL: {str(e)}")
        raise e

if __name__ == '__main__':
    main()
