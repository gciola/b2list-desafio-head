import pandas as pd
import boto3
import os
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
        """Baixa do S3 e normaliza cabeçalhos e separadores"""
        print(f"  -> Baixando {key}...")
        obj = s3_client.get_object(Bucket=bucket, Key=key)
        # Seus arquivos usam ';' como separador
        df = pd.read_csv(obj['Body'], sep=';')
        # Normaliza colunas para evitar erros de case-sensitivity
        df.columns = df.columns.str.strip().str.upper()
        return df
    
    try:
        # 2. Carregamento das Fontes
        df_maestro = get_df('Maestro.csv')
        df_associados = get_df('Associados.csv')
        df_terceros = get_df('Terceros.csv')

        # 3. Joins Estratégicos (Maestro como Âncora)
        # Primeiro merge com Associados
        pharmacy = df_maestro.merge(df_associados, on='ID', how='left', suffixes=('', '_ASSOC'))
        
        # Segundo merge com Terceros
        pharmacy = pharmacy.merge(df_terceros, on='ID', how='left', suffixes=('', '_TERC'))
        
        print("  -> Joins realizados. Iniciando mapeamento de campos...")

        # 4. Construção das Colunas Finais (Lógica de Precedência)
        # Trade Name: Prioridade para Associado, depois Terceiro
        pharmacy['trade_name'] = pharmacy['NOME_ASSOC'].fillna(pharmacy['NOME_TERC'])
        
        # NIT e Razão Social vêm exclusivamente do Maestro
        pharmacy['corporate_name'] = pharmacy['NOME_FANTASIA']
        pharmacy['nit'] = pharmacy['NIT']
        pharmacy['code_pharmacy'] = pharmacy['ID']
        
        # Coordenadas: Prioridade para Associado (usando verificação de colunas para evitar KeyError)
        col_lat_assoc = 'LATITUDE_ASSOC' if 'LATITUDE_ASSOC' in pharmacy.columns else 'LATITUDE'
        col_lon_assoc = 'LONGITUDE_ASSOC' if 'LONGITUDE_ASSOC' in pharmacy.columns else 'LONGITUDE'
        
        pharmacy['lat'] = pharmacy[col_lat_assoc].fillna(pharmacy['LATITUDE_TERC'])
        pharmacy['lon'] = pharmacy[col_lon_assoc].fillna(pharmacy['LONGITUDE_TERC'])
        
        # Categoria: Identificada pela origem do registro
        pharmacy['category'] = pharmacy['NOME_ASSOC'].isna().map({True: 'TERCERO', False: 'ASSOCIADO'})
        
        # 5. Regra de Negócio: Enabled (Regex nos campos de Observação)
        obs_col = 'OBSERVACAO_ASSOC' if 'OBSERVACAO_ASSOC' in pharmacy.columns else 'OBSERVACAO'
        observacao = pharmacy[obs_col].fillna(pharmacy['OBSERVACAO_TERC'])
        termos = r'Em dia|Ativo|Cadastro Ativo|Verificado|Vigente'
        pharmacy['enabled'] = observacao.str.contains(termos, case=False, na=False, regex=True)
        
        # 6. Seleção e Limpeza Final
        final = pharmacy[[
            'code_pharmacy', 'nit', 'trade_name', 'corporate_name', 
            'lat', 'lon', 'category', 'enabled'
        ]]
        
        # 7. Exportação e Upload para S3
        csv_buffer = StringIO()
        final.to_csv(csv_buffer, index=False)
        
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