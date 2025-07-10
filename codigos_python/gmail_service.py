from datetime import datetime
from auth_service import autenticar_gmail

class GmailService:
    def __init__(self):
        self.service = None
        self.last_check_time = None
        self.last_filter = None
        self.cached_emails = []

    def get_email_details(self, email_id):
        """Pega detalhes de um email específico"""
        try:
            dados = self.service.users().messages().get(
                userId='me',
                id=email_id,
                format='metadata',
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()

            cabecalhos = {h['name']: h['value'] for h in dados['payload']['headers']}
            
            # Extrair apenas o endereço de email do campo From
            from_field = cabecalhos.get('From', 'Desconhecido')
            if '<' in from_field and '>' in from_field:
                # Formato: "Nome <email@domain.com>"
                email_address = from_field.split('<')[1].split('>')[0]
            else:
                # Formato direto: "email@domain.com"
                email_address = from_field

            return {
                "remetente": email_address,
                "assunto": cabecalhos.get('Subject', 'Sem assunto'),
                "data": cabecalhos.get('Date', ''),
                "id": email_id
            }
        except Exception as e:
            print(f"Erro ao buscar email {email_id}: {e}")
            return None

    def buscar_emails_recentes(self, filtro=None, max_results=7):
        """
        Busca emails recentes baseado no filtro
        Args:
            filtro: remetente específico ou None para emails não lidos
            max_results: quantidade máxima de emails
        """
        if not self.service:
            self.service = autenticar_gmail()
            if not self.service:
                return self.cached_emails # Retorna cache se autenticação falhar

        try:
            # Construir query
            if filtro and filtro.strip():
                query = f"from:{filtro}"
                self.last_filter = filtro
            else:
                query = "is:unread"
                self.last_filter = None

            # Buscar mensagens
            response = self.service.users().messages().list(
                userId='me',
                maxResults=max_results,
                q=query
            ).execute()

            mensagens = response.get('messages', [])
            emails = []

            # Pegar detalhes de cada email
            for mensagem in mensagens[:max_results]:
                email_details = self.get_email_details(mensagem['id'])
                if email_details:
                    emails.append(email_details)

            # Atualizar cache e timestamp
            self.cached_emails = emails
            self.last_check_time = datetime.now()

            return emails

        except Exception as e:
            print(f"Erro ao buscar emails: {e}")
            return self.cached_emails  # Retorna cache em caso de erro

    def buscar_novos_emails_desde_ultima_checagem(self):
        """
        Busca apenas emails novos desde a última checagem
        Usado no ciclo de atualização automática
        """
        if not self.service:
            self.service = autenticar_gmail()
            if not self.service:
                return self.cached_emails

        try:
            # Se nunca checou antes, busca os 5 mais recentes
            if not self.last_check_time:
                return self.buscar_emails_recentes(self.last_filter)

            # Construir query com filtro de tempo
            time_filter = self.last_check_time.strftime('%Y/%m/%d')

            if self.last_filter:
                query = f"from:{self.last_filter} after:{time_filter}"
            else:
                query = f"is:unread after:{time_filter}"

            response = self.service.users().messages().list(
                userId='me',
                maxResults=10,
                q=query
            ).execute()

            mensagens = response.get('messages', [])
            novos_emails = []

            # Pegar apenas emails realmente novos (não estão no cache)
            cached_ids = {email['id'] for email in self.cached_emails}

            for mensagem in mensagens:
                if mensagem['id'] not in cached_ids:
                    email_details = self.get_email_details(mensagem['id'])
                    if email_details:
                        novos_emails.append(email_details)

            # Combinar novos emails com cache (manter os 5 mais recentes)
            todos_emails = novos_emails + self.cached_emails
            self.cached_emails = todos_emails[:7]
            self.last_check_time = datetime.now()

            return self.cached_emails

        except Exception as e:
            print(f"Erro ao buscar novos emails: {e}")
            return self.cached_emails

    def reset_filter(self, novo_filtro=None):
        """
        Reseta o filtro e busca emails com nova configuração
        Chamado quando dashboard.json é atualizado
        """
        print(f"Gmail: Aplicando novo filtro - {novo_filtro}")
        self.last_filter = novo_filtro
        self.last_check_time = None  # Reset para buscar tudo novamente
        return self.buscar_emails_recentes(novo_filtro)

# Instância global do serviço
gmail_service = GmailService()

def get_gmail_data(widget_config):
    """
    Função principal para integração com o dashboard
    Args:
        widget_config: configuração do widget (contém filtro do remetente)
    """
    filtro = widget_config.get("remetente", "")

    # Se o filtro mudou, reset e busca novamente
    if filtro != gmail_service.last_filter:
        emails = gmail_service.reset_filter(filtro)
    else:
        # Busca apenas novos emails desde última checagem
        emails = gmail_service.buscar_novos_emails_desde_ultima_checagem()

    return {
        "emails": emails[:7],  # Sempre retorna máximo 5
        "filtro_atual": gmail_service.last_filter,
        "ultima_atualizacao": gmail_service.last_check_time.isoformat() if gmail_service.last_check_time else None
    }

# Para teste individual
if __name__ == "__main__":
    # Teste da funcionalidade
    print("Testando Gmail Service...")

    # Primeira busca
    config = {"remetente": "lfcfrontin"}  # Buscar emails não lidos
    resultado = get_gmail_data(config)
    print(f"Emails encontrados: {len(resultado['emails'])}")

    for email in resultado['emails']:
        print(f"- {email['remetente']}: {email['assunto']}")