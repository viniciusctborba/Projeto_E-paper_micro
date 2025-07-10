import os
import json
from datetime import datetime, timedelta, timezone
from google.oauth2 import service_account
from googleapiclient.discovery import build

class CalendarService:
    def __init__(self):
        self.service = None
        self.credentials_file = 'credentials.json'
        self.cached_events = []
        self.last_check_time = None
        self.eventos_mostrados = set()  # Para controlar eventos já processados
        
        # ID da agenda TRABALHOS PUC (do seu código original)
        self.id_agenda_puc = 'pt.brazilian#holiday@group.v.calendar.google.com'
        
    def autenticar(self):
        """Autentica usando service account"""
        try:
            if not os.path.exists(self.credentials_file):
                print(f"Arquivo {self.credentials_file} não encontrado")
                return None
                
            credencial = service_account.Credentials.from_service_account_file(
                self.credentials_file,
                scopes=['https://www.googleapis.com/auth/calendar.readonly']
            )
            
            self.service = build('calendar', 'v3', credentials=credencial)
            return self.service
            
        except Exception as e:
            print(f"Erro na autenticação do Calendar: {e}")
            return None

    def buscar_eventos_agenda_puc(self, data_inicial=None, data_final=None, filtro_titulo=None, max_results=10):
        """
        Busca eventos da agenda PUC específica
        Args:
            data_inicial: data de início (default: hoje)
            data_final: data final (default: None)
            filtro_titulo: filtro por título
            max_results: quantidade máxima de eventos
        """
        if not self.service:
            if not self.autenticar():
                return self.cached_events
        
        try:
            # Definir data inicial
            if not data_inicial:
                data_inicial = datetime.now(timezone.utc)
            elif isinstance(data_inicial, str):
                data_inicial = datetime.strptime(data_inicial, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            
            time_min = data_inicial.isoformat()
            
            # Parâmetros da consulta
            parametros = {
                'calendarId': self.id_agenda_puc,
                'timeMin': time_min,
                'singleEvents': True,
                'orderBy': 'startTime',
                'maxResults': max_results
            }
            
            # Adicionar data final se especificada
            if data_final:
                if isinstance(data_final, str):
                    data_final = datetime.strptime(data_final, '%Y-%m-%d').replace(tzinfo=timezone.utc)
                    data_final = data_final.replace(hour=23, minute=59, second=59)
                parametros['timeMax'] = data_final.isoformat()
            
            # Buscar eventos
            resposta = self.service.events().list(**parametros).execute()
            eventos = resposta.get('items', [])
            
            eventos_formatados = []
            
            for evento in eventos:
                # Aplicar filtro de título se especificado
                titulo = evento.get('summary', 'Sem título')
                if filtro_titulo and filtro_titulo.lower() not in titulo.lower():
                    continue
                
                # Extrair informações do evento
                start = evento['start'].get('dateTime', evento['start'].get('date'))
                
                # Formatear data e hora
                if 'T' in start:  # Evento com horário específico
                    start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    data_evento = start_dt.strftime('%Y-%m-%d')
                    hora_evento = start_dt.strftime('%H:%M')
                else:  # Evento de dia inteiro
                    data_evento = start
                    hora_evento = "Dia inteiro"
                
                eventos_formatados.append({
                    "titulo": titulo,
                    "data": data_evento,
                    "hora": hora_evento,
                    "descricao": evento.get('description', ''),
                    "localizacao": evento.get('location', ''),
                    "id": evento.get('id', ''),
                    "calendario": "PUC Trabalhos"
                })
            
            # Atualizar cache
            self.cached_events = eventos_formatados
            self.last_check_time = datetime.now()
            
            return eventos_formatados
            
        except Exception as e:
            print(f"Erro ao buscar eventos da agenda PUC: {e}")
            return self.cached_events

    def buscar_eventos_proximos(self, data_inicial=None, data_final=None, max_results=10):
        """
        Busca eventos próximos do calendário principal (original)
        Args:
            data_inicial: data de início (default: hoje)
            data_final: data final (default: hoje + 7 dias)
            max_results: quantidade máxima de eventos
        """
        if not self.service:
            if not self.autenticar():
                return self.cached_events
        
        try:
            # Definir período de busca
            if not data_inicial:
                data_inicial = datetime.now()
            if not data_final:
                data_final = data_inicial + timedelta(days=7)
            
            # Converter para formato ISO
            time_min = data_inicial.isoformat() + 'Z'
            time_max = data_final.isoformat() + 'Z'
            
            # Buscar eventos do calendário principal
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            eventos_formatados = []
            
            for event in events:
                # Extrair informações do evento
                start = event['start'].get('dateTime', event['start'].get('date'))
                
                # Formatear datas
                if 'T' in start:  # Evento com horário
                    start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    data_evento = start_dt.strftime('%Y-%m-%d')
                    hora_evento = start_dt.strftime('%H:%M')
                else:  # Evento de dia inteiro
                    data_evento = start
                    hora_evento = "Dia inteiro"
                
                eventos_formatados.append({
                    "titulo": event.get('summary', 'Sem título'),
                    "data": data_evento,
                    "hora": hora_evento,
                    "descricao": event.get('description', ''),
                    "localizacao": event.get('location', ''),
                    "id": event.get('id', ''),
                    "calendario": "Principal"
                })
            
            return eventos_formatados
            
        except Exception as e:
            print(f"Erro ao buscar eventos do calendário principal: {e}")
            return self.cached_events

    def buscar_novos_eventos_desde_ultima_checagem(self, filtro_titulo=None):
        """
        Busca apenas eventos novos desde a última checagem (similar ao loop do código original)
        """
        if not self.service:
            if not self.autenticar():
                return []
        
        try:
            # Se nunca checou antes, busca eventos dos próximos 30 dias
            if not self.last_check_time:
                data_inicial = datetime.now(timezone.utc)
                data_final = data_inicial + timedelta(days=30)
            else:
                # Busca desde a última checagem
                data_inicial = self.last_check_time
                data_final = data_inicial + timedelta(days=30)
            
            # Buscar eventos da agenda PUC
            parametros = {
                'calendarId': self.id_agenda_puc,
                'timeMin': data_inicial.isoformat(),
                'timeMax': data_final.isoformat(),
                'singleEvents': True,
                'orderBy': 'startTime',
                'maxResults': 50
            }
            
            resposta = self.service.events().list(**parametros).execute()
            eventos = resposta.get('items', [])
            
            novos_eventos = []
            
            for evento in eventos:
                id_evento = evento['id']
                titulo = evento.get('summary', '').lower()
                
                # Verificar se é novo evento e se atende ao filtro
                if id_evento not in self.eventos_mostrados:
                    if not filtro_titulo or filtro_titulo.lower() in titulo:
                        # Formatear evento
                        start = evento['start'].get('dateTime', evento['start'].get('date'))
                        
                        if 'T' in start:
                            start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                            data_evento = start_dt.strftime('%Y-%m-%d')
                            hora_evento = start_dt.strftime('%H:%M')
                        else:
                            data_evento = start
                            hora_evento = "Dia inteiro"
                        
                        evento_formatado = {
                            "titulo": evento.get('summary', 'Sem título'),
                            "data": data_evento,
                            "hora": hora_evento,
                            "descricao": evento.get('description', ''),
                            "id": id_evento,
                            "calendario": "PUC Trabalhos"
                        }
                        
                        novos_eventos.append(evento_formatado)
                        self.eventos_mostrados.add(id_evento)
            
            self.last_check_time = datetime.now(timezone.utc)
            return novos_eventos
            
        except Exception as e:
            print(f"Erro ao buscar novos eventos: {e}")
            return []

# Instância global do serviço
calendar_service = CalendarService()

def get_calendar_data(widget_config):
    """
    Função principal para integração com o dashboard
    Args:
        widget_config: configuração do widget
    """
    try:
        # Verificar configuração
        data_inicial = widget_config.get("data_inicial")
        data_final = widget_config.get("data_final") 
        titulo_filtro = widget_config.get("titulo_evento")
        calendario_tipo = widget_config.get("calendario", "puc")  # "puc" ou "principal"
        
        # Escolher qual calendário usar
        if calendario_tipo.lower() == "principal":
            # Calendário principal (original)
            if data_inicial and data_final:
                dt_inicial = datetime.strptime(data_inicial, '%Y-%m-%d')
                dt_final = datetime.strptime(data_final, '%Y-%m-%d')
                eventos = calendar_service.buscar_eventos_proximos(dt_inicial, dt_final)
            else:
                eventos = calendar_service.buscar_eventos_proximos()
            
            # Filtrar por título se especificado
            if titulo_filtro:
                eventos = [e for e in eventos if titulo_filtro.lower() in e['titulo'].lower()]
        
        else:
            # Agenda PUC (padrão)
            if data_inicial == "-":
                data_inicial = None
            if data_final == "-":
                data_final = None
            if titulo_filtro == "-":
                titulo_filtro = None
                
            eventos = calendar_service.buscar_eventos_agenda_puc(
                data_inicial=data_inicial,
                data_final=data_final, 
                filtro_titulo=titulo_filtro,
                max_results=10
            )
        
        # Formato de retorno para o dashboard
        if eventos:
            return {
                "eventos": eventos[:7],  # Máximo 5 eventos
                "proximo_evento": eventos[0],  # Próximo evento principal
                "total_eventos": len(eventos),
                "calendario_tipo": calendario_tipo
            }
        else:
            return {
                "eventos": [],
                "proximo_evento": {
                    "titulo": "Nenhum evento encontrado",
                    "data": datetime.now().strftime('%Y-%m-%d'),
                    "hora": "--:--",
                    "calendario": calendario_tipo
                },
                "total_eventos": 0,
                "calendario_tipo": calendario_tipo
            }
            
    except Exception as e:
        print(f"Erro no Calendar Service: {e}")
        return {
            "eventos": [],
            "proximo_evento": {
                "titulo": "Erro ao carregar agenda",
                "data": datetime.now().strftime('%Y-%m-%d'),
                "hora": "--:--"
            },
            "total_eventos": 0,
            "calendario_tipo": "erro"
        }

def get_new_calendar_events(widget_config):
    """
    Função para buscar apenas novos eventos (usada no ciclo de atualização)
    """
    try:
        titulo_filtro = widget_config.get("titulo_evento")
        if titulo_filtro == "-":
            titulo_filtro = None
            
        novos_eventos = calendar_service.buscar_novos_eventos_desde_ultima_checagem(titulo_filtro)
        
        return {
            "novos_eventos": novos_eventos,
            "quantidade_novos": len(novos_eventos)
        }
        
    except Exception as e:
        print(f"Erro ao buscar novos eventos: {e}")
        return {
            "novos_eventos": [],
            "quantidade_novos": 0
        }

# Para teste individual
if __name__ == "__main__":
    print("Testando Calendar Service...")
    
    # Teste básico
    config = {}
    resultado = get_calendar_data(config)
    
    print(f"Eventos encontrados: {len(resultado['eventos'])}")
    print(f"Próximo evento: {resultado['proximo_evento']['titulo']}")
    
    for evento in resultado['eventos']:
        print(f"- {evento['data']} {evento['hora']}: {evento['titulo']}")