import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

def autenticar_gmail():
    """
    Autentica no Gmail usando token.json ou criando novo token
    Retorna o serviço do Gmail ou None se falhar
    """
    escopos = ['https://www.googleapis.com/auth/gmail.readonly']
    credenciais = None
    
    # Verifica se já existe token
    if os.path.exists('token.json'):
        try:
            credenciais = Credentials.from_authorized_user_file('token.json', escopos)
        except Exception as e:
            print(f"Erro ao carregar token existente: {e}")
            # Remove token corrompido
            try:
                os.remove('token.json')
            except:
                pass
    
    # Se não há credenciais válidas, cria novas
    if not credenciais or not credenciais.valid:
        if credenciais and credenciais.expired and credenciais.refresh_token:
            try:
                credenciais.refresh(Request())
            except Exception as e:
                print(f"Erro ao atualizar token: {e}")
                credenciais = None
        
        if not credenciais:
            # Lista todos os arquivos JSON para debug
            json_files = [f for f in os.listdir('.') if f.endswith('.json')]
            print(f"Arquivos JSON encontrados: {json_files}")
            
            # Precisa fazer login
            if not os.path.exists('credentials_gmail.json'):
                print("Erro: 'credentials_gmail.json' não encontrado.")
                return None
            
            # Debug: verificar o conteúdo do credentials_gmail.json
            try:
                with open('credentials_gmail.json', 'r') as f:
                    cred_data = json.load(f)
                    print("Estrutura do credentials_gmail.json:")
                    print(f"Chaves principais: {list(cred_data.keys())}")
                    
                    if 'installed' in cred_data:
                        print("✓ Tem chave 'installed'")
                        installed = cred_data['installed']
                        required_keys = ['client_id', 'client_secret', 'auth_uri', 'token_uri']
                        for key in required_keys:
                            if key in installed:
                                print(f"✓ Tem {key}")
                            else:
                                print(f"✗ Falta {key}")
                    else:
                        print("✗ Não tem chave 'installed'")
                        print("ESTE NÃO É O ARQUIVO CORRETO!")
                        print("Você precisa usar o arquivo OAuth2, não Service Account")
                        
            except Exception as e:
                print(f"Erro ao ler credentials_gmail.json: {e}")
                return None
            
            try:
                flow = InstalledAppFlow.from_client_secrets_file('credentials_gmail.json', escopos)
                credenciais = flow.run_local_server(port=0)
            except Exception as e:
                print(f"Erro durante autenticação: {e}")
                return None
        
        # Salva as credenciais
        try:
            with open('token.json', 'w') as token:
                token.write(credenciais.to_json())
        except Exception as e:
            print(f"Erro ao salvar token: {e}")
    
    # Cria o serviço
    try:
        service = build('gmail', 'v1', credentials=credenciais)
        return service
    except Exception as e:
        print(f"Erro ao criar serviço do Gmail: {e}")
        return None