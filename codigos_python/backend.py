import json
import time
import threading
import os
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Imports das suas APIs existentes
from weather_service import get_weather
from news_service import get_global_news
from reddit_service import RedditHeadlineFetcher
# from twitter import buscar_tweets
from gmail_service import get_gmail_data
from calendar_service import get_calendar_data, get_new_calendar_events
from mqtt_sender import connect_mqtt, send_layout_to_esp32, get_mqtt_client_status

class DashboardAPI:
    def __init__(self):
        self.config_file = 'dashboard.json'  # Arquivo de configuração (entrada)
        self.output_file = 'output.json'     # Arquivo de saída para Arduino
        self.running = False
        self.update_interval = 300 # Intervalo de atualização em segundos (5 minutos)
        self.scheduler_thread = None
        self.time_monitor_thread = None  # Nova thread para monitorar tempo
        self.file_observer = None
        self.first_run = True  # Para controlar primeira execução
        self.last_minute = -1  # Para controlar mudanças de minuto
        
        # Debounce para file watcher
        self.last_file_change = 0
        self.debounce_delay = 1.0  # 1 segundo de delay
        self.file_change_lock = threading.Lock()
        
        # Cache para dados
        self.cache = {}
        
        # Inicializar services
        self.reddit_fetcher = RedditHeadlineFetcher()
        # Gmail e Calendar services são importados como funções
        
    def load_config(self):
        """Carrega configuração do dashboard.json (entrada)"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar config: {e}")
            return None
    
    def load_output_data(self):
        """Carrega dados do output.json para atualização"""
        try:
            with open(self.output_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar output.json: {e}")
            return None
    
    def save_output_data(self, data_with_real_info):
        """Salva output.json com dados atualizados (saída para Arduino) e envia via MQTT"""
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(data_with_real_info, f, indent=2, ensure_ascii=False)
            print(f"Output.json atualizado: {datetime.now()}")
            # Enviar via MQTT sempre que salvar
            if not get_mqtt_client_status():
                print("[MQTT] Não conectado, tentando conectar...")
                if not connect_mqtt():
                    print("[MQTT] Falha ao conectar, não foi possível enviar o output.json via MQTT.")
                    return True  # Arquivo foi salvo, mas MQTT falhou
            if send_layout_to_esp32(self.output_file):
                print("[MQTT] output.json enviado via MQTT com sucesso!")
            else:
                print("[MQTT] Falha ao enviar output.json via MQTT.")
            return True
        except Exception as e:
            print(f"Erro ao salvar output.json: {e}")
            return False
    
    def increment_time_in_clima_widget(self, widget_data):
        """Incrementa +1 minuto no horário atual do widget de clima sem recalcular fusos"""
        try:
            # Verificar se existe campo hora
            if "hora" in widget_data:
                current_hora = widget_data["hora"]
                
                # Parse do horário atual (formato HH:MM)
                if isinstance(current_hora, str) and ":" in current_hora:
                    try:
                        hora_parts = current_hora.split(":")
                        horas = int(hora_parts[0])
                        minutos = int(hora_parts[1])
                        
                        # Incrementar 1 minuto
                        minutos += 1
                        
                        # Se passou de 59 minutos, zerar minutos e incrementar hora
                        if minutos >= 60:
                            minutos = 0
                            horas += 1
                            
                            # Se passou de 23 horas, voltar para 00
                            if horas >= 24:
                                horas = 0
                        
                        # Formatar de volta para HH:MM
                        nova_hora = f"{horas:02d}:{minutos:02d}"
                        widget_data["hora"] = nova_hora
                        
                        print(f"    Horário atualizado: {current_hora} → {nova_hora}")
                        
                    except (ValueError, IndexError) as e:
                        print(f"    ⚠ Erro ao parse do horário '{current_hora}': {e}")
                else:
                    print(f"    ⚠ Formato de horário inválido: '{current_hora}'")
            
            # Atualizar data apenas se necessário (pode manter a mesma lógica simples)
            if "data" in widget_data:
                # Manter a data atual do sistema
                now = datetime.now()
                widget_data["data"] = now.strftime("%Y-%m-%d")
                
        except Exception as e:
            print(f"    ✗ Erro ao incrementar horário: {e}")
    
    def update_times_only(self):
        """Atualiza apenas os horários nos widgets de clima no output.json existente"""
        try:
            # Carregar dados atuais do output.json
            output_data = self.load_output_data()
            if not output_data:
                print("Não foi possível carregar output.json para atualização de horário")
                return
            
            print(f"[Time Update] Atualizando horários dos widgets de clima - {datetime.now().strftime('%H:%M')}")
            
            widgets_clima_atualizados = 0
            
            # Percorrer todas as páginas e widgets para atualizar apenas widgets de clima
            for i, pagina in enumerate(output_data.get("paginas", [])):
                for j, widget in enumerate(pagina.get("widgets", [])):
                    widget_tipo = widget.get("tipo", "").lower()
                    
                    # Verificar se é um widget de clima
                    if widget_tipo == "clima":
                        widget_data = widget.get("dados", {})
                        if widget_data:
                            cidade = widget_data.get("cidade", "Desconhecida")
                            hora_atual = widget_data.get("hora", "N/A")
                            print(f"    Widget clima {j+1} da página {i+1} ({cidade}): {hora_atual}")
                            
                            self.increment_time_in_clima_widget(widget_data)
                            widgets_clima_atualizados += 1
            
            # Salvar dados atualizados apenas se houve widgets de clima
            if widgets_clima_atualizados > 0:
                if self.save_output_data(output_data):
                    print(f"[Time Update] ✓ {widgets_clima_atualizados} widgets de clima atualizados com sucesso")
                else:
                    print(f"[Time Update] ✗ Falha ao salvar horários dos widgets de clima")
            else:
                print(f"[Time Update] ⚠ Nenhum widget de clima encontrado para atualizar")
                
        except Exception as e:
            print(f"[Time Update] ✗ Erro na atualização de horários dos widgets de clima: {e}")
    
    def time_monitor_loop(self):
        """Loop para monitorar mudanças de minuto"""
        while self.running:
            try:
                current_minute = datetime.now().minute
                
                # Verificar se o minuto mudou
                if self.last_minute != -1 and current_minute != self.last_minute:
                    # Minuto mudou, atualizar apenas horários
                    self.update_times_only()
                
                self.last_minute = current_minute
                
                # Verificar a cada segundo para detectar mudança de minuto rapidamente
                time.sleep(1)
                
            except Exception as e:
                print(f"[Time Monitor] Erro: {e}")
                time.sleep(1)
    
    def fetch_weather_data(self, widget_data):
        """Busca dados do clima usando sua função get_weather() original"""
        try:
            location = widget_data.get("regiao", "Rio de Janeiro")
            print(f"Clima: Buscando dados para {location}")
            
            weather = get_weather(location)
            
            if weather:
                print(f"Clima: ✓ Dados obtidos - {weather['temp']}°C")
                return {
                    "temperatura": weather["temp"],
                    "previsao": weather["condition"],
                    "cidade": location,
                    "data": weather["date"],
                    "hora": weather["time"]
                }
            else:
                print("Clima: ✗ Erro ao obter dados")
                
        except Exception as e:
            print(f"Clima: ✗ Erro no processamento: {e}")
        
        # Fallback em caso de erro
        cidade_padrao = widget_data.get("regiao", "Rio de Janeiro")
        fallback_data = {
            "temperatura": "N/A",
            "previsao": "Indisponível", 
            "cidade": cidade_padrao,
            "data": "N/A",
            "hora": "N/A"
        }
        
        print(f"Clima: Usando dados de fallback para {cidade_padrao}")
        return fallback_data
    
    def fetch_email_data(self, widget_data):
        """Busca dados do Gmail usando gmail_service.py"""
        try:
            resultado = get_gmail_data(widget_data)
            return resultado
        except Exception as e:
            print(f"Erro no email: {e}")
        return self.cache.get('email', {"emails": []})
        
    def fetch_news_data(self, widget_data):
        """Busca notícias usando sua função get_global_news() original"""
        print("DEBUG 1")
        tema = widget_data.get("tema", "brasil")
        try:
            print(f"Notícias: Buscando tema '{tema}'")
            
            noticias = get_global_news(tema)
            print("DEBUG 2")
            
            if noticias:
                print(f"Notícias: ✓ {len(noticias)} notícias encontradas")
                # Se encontrou notícias, retorne os dados corretos e saia da função
                return {
                    "tema": tema,
                    "noticias": noticias
                }
            else:
                print("Notícias: ✗ NewsAPI retornou 0 resultados, usando fallback.")
                # Se não encontrou, retorne o fallback e saia da função
                return {
                    "tema": tema,
                    "noticias": ["Nenhuma notícia encontrada"]
                }
                
        except Exception as e:
            print(f"Notícias: ✗ Erro: {e}, usando fallback.")
            # Se deu erro, retorne o fallback e saia da função
            return {
                "tema": tema,
                "noticias": ["Erro ao buscar notícias"]
            }
    
    def fetch_reddit_data(self, widget_data):
        """Busca dados do Reddit usando reddit_service.py"""
        try:
            # Obter configurações do widget
            subreddits = widget_data.get("subreddits", ["technology"])
            limit = widget_data.get("limit", 7)
            time_filter = widget_data.get("time_filter", "week")
            
            # Se subreddits é uma string, converter para lista
            if isinstance(subreddits, str):
                subreddits = [subreddits]
            
            print(f"Reddit: Buscando posts de {subreddits} (limit: {limit})")
            
            # Buscar headlines usando o Reddit service
            headlines = self.reddit_fetcher.get_headlines(subreddits, limit=limit, time_filter=time_filter)
            
            if headlines:
                # Formatear dados no formato solicitado
                posts = []
                for post in headlines[:limit]:  # Limitar ao número solicitado
                    posts.append({
                        "titulo": post['title'],
                        "upvotes": post['score'],
                        "comentarios": post['comments']
                    })
                
                # Usar o primeiro subreddit como referência
                subreddit_name = f"r/{subreddits[0]}"
                
                resultado = {
                    "subreddit": subreddit_name,
                    "posts": posts
                }
                
                print(f"Reddit: ✓ {len(posts)} posts obtidos de {subreddit_name}")
                return resultado
            else:
                print("Reddit: ✗ Nenhum post encontrado")
                
        except Exception as e:
            print(f"Reddit: ✗ Erro: {e}")
        
        # Fallback em caso de erro
        subreddit_padrao = widget_data.get("subreddits", ["technology"])
        if isinstance(subreddit_padrao, list):
            subreddit_padrao = subreddit_padrao[0]
        
        fallback_data = {
            "subreddit": f"r/{subreddit_padrao}",
            "posts": [
                {"titulo": "Erro ao buscar posts do Reddit", "upvotes": 0, "comentarios": 0}
            ]
        }
        
        print(f"Reddit: Usando dados de fallback para r/{subreddit_padrao}")
        return fallback_data
    
    def fetch_twitter_data(self, widget_data):
        """Busca dados do Twitter - TEMPORARIAMENTE DESABILITADO"""
        print("Twitter temporariamente desabilitado (rate limit)")
        return self.cache.get('twitter', {
            "tweets": ["Twitter temporariamente indisponível"]
        })
    
    def fetch_calendar_data(self, widget_data, is_update_cycle=False):
        """Busca dados do calendário usando calendar_service.py"""
        try:
            if is_update_cycle and not self.first_run:
                # No ciclo de atualização, busca apenas novos eventos
                print(widget_data)
                resultado = get_new_calendar_events(widget_data)
                if resultado['quantidade_novos'] > 0:
                    print(f"Novos eventos encontrados: {resultado['quantidade_novos']}")
                return resultado
            else:
                # Primeira execução ou mudança de configuração
                resultado = get_calendar_data(widget_data)
                
                # Formatar os eventos no formato solicitado
                if resultado and 'eventos' in resultado:
                    eventos_originais = resultado.get('eventos', [])
                    
                    if not eventos_originais:
                        return {
                            "eventos": []
                        }
                    
                    # Formatar eventos no novo formato
                    eventos_formatados = []
                    for evento in eventos_originais:
                        data_original = evento.get('data', '')
                        hora = evento.get('hora', '')
                        titulo = evento.get('titulo', 'Sem título')
                        
                        # Converter data de YYYY-MM-DD para DD/MM
                        try:
                            if len(data_original) >= 10:  # formato YYYY-MM-DD
                                partes_data = data_original.split('-')
                                if len(partes_data) >= 3:
                                    data_formatada = f"{partes_data[2]}/{partes_data[1]}"
                                else:
                                    data_formatada = data_original
                            else:
                                data_formatada = data_original
                        except:
                            data_formatada = data_original
                        
                        # Formatar hora
                        if hora == "Dia inteiro":
                            hora_formatada = "Dia inteiro"
                        else:
                            hora_formatada = hora
                        
                        evento_formatado = {
                            "evento": titulo,
                            "data": data_formatada,
                            "hora": hora_formatada
                        }
                        
                        eventos_formatados.append(evento_formatado)
                    
                    return {
                        "eventos": eventos_formatados
                    }
                    
                return resultado
        except Exception as e:
            print(f"Erro no calendário: {e}")
        return self.cache.get('calendar', {
            "eventos": []
        })
    
    def fetch_reminder_data(self, widget_data):
        """Dados de lembrete - pode ser implementado com arquivo local"""
        return {
            "lembretes": [
                {"texto": "Comprar leite", "ok": False},
                {"texto": "Ligar dentista", "ok": True}
            ]
        }
    
    def process_widget(self, widget, is_update_cycle=False):
        """Processa um widget individual e busca seus dados"""
        widget_type = widget["tipo"].lower()
        widget_data = widget.get("dados", {})
        
        data_fetchers = {
            "clima": self.fetch_weather_data,
            "email": self.fetch_email_data,
            "notícias": self.fetch_news_data,
            "reddit": self.fetch_reddit_data,
            "twitter": self.fetch_twitter_data,
            "eventos": lambda wd: self.fetch_calendar_data(wd, is_update_cycle),
            "lembrete": self.fetch_reminder_data
        }
        
        fetcher = data_fetchers.get(widget_type)
        if fetcher:
            new_data = fetcher(widget_data)
            if new_data:
                # Atualizar cache
                self.cache[widget_type] = new_data
                # Atualizar widget com dados frescos
                widget["dados"] = new_data
        
        return widget
    
    def update_dashboard_data(self, source="scheduled"):
        """Lê dashboard.json, atualiza dados e salva em output.json"""
        config = self.load_config()
        if not config:
            print("Não foi possível carregar configuração")
            return
        
        source_text = "configuração alterada" if source == "file_change" else "atualização programada"
        print(f"\n--- Atualizando dados ({source_text})... {datetime.now()} ---")
        print(f"Entrada: {self.config_file} → Saída: {self.output_file}")
        
        is_update_cycle = not self.first_run
        widgets_processados = 0
        
        # Criar cópia da configuração para output
        output_data = json.loads(json.dumps(config))  # Deep copy
        
        # Processar cada página
        for i, pagina in enumerate(output_data.get("paginas", [])):
            print(f"Processando página {i+1}")
            for j, widget in enumerate(pagina.get("widgets", [])):
                widget_tipo = widget.get("tipo", "desconhecido")
                print(f"  Widget {j+1}: {widget_tipo}")
                
                try:
                    # Processar widget e atualizar dados
                    updated_widget = self.process_widget(widget, is_update_cycle)
                    # O widget já foi atualizado por referência
                    widgets_processados += 1
                    print(f"    ✓ {widget_tipo} processado com sucesso")
                except Exception as e:
                    print(f"    ✗ Erro no widget {widget_tipo}: {e}")
        
        # Salvar dados atualizados em output.json
        if self.save_output_data(output_data):
            if self.first_run:
                print(f"✓ Primeira execução - {widgets_processados} widgets carregados")
                self.first_run = False
            else:
                print(f"✓ Dados atualizados - {widgets_processados} widgets processados")
            print(f"✓ Arduino pode ler dados de: {self.output_file}")
        else:
            print("✗ Falha ao salvar output.json")
            
        print("--- Fim da atualização ---\n")
    
    def scheduler_loop(self):
        """Loop principal de atualização"""
        while self.running:
            self.update_dashboard_data("scheduled")
            time.sleep(self.update_interval)
    
    def handle_file_change(self):
        """Processa mudança de arquivo com debounce"""
        with self.file_change_lock:
            current_time = time.time()
            
            # Se a última mudança foi muito recente, ignora
            if current_time - self.last_file_change < self.debounce_delay:
                print(f"[File Watcher] Mudança ignorada (debounce) - {datetime.now()}")
                return
            
            self.last_file_change = current_time
            
        print(f"[File Watcher] Nova configuração detectada! - {datetime.now()}")
        print("Reprocessando dados e atualizando output.json...")
        
        # Reset flag para nova configuração
        self.first_run = True
        # Atualização imediata com nova config
        self.update_dashboard_data("file_change")
    
    def start_monitoring(self):
        """Inicia monitoramento e atualizações automáticas"""
        print("Iniciando monitoramento do dashboard...")
        self.running = True
        
        # Thread para atualizações periódicas
        self.scheduler_thread = threading.Thread(target=self.scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        # Thread para monitoramento de mudanças de minuto
        self.time_monitor_thread = threading.Thread(target=self.time_monitor_loop, daemon=True)
        self.time_monitor_thread.start()
        
        # Monitor de arquivo para detectar mudanças na configuração
        self.setup_file_monitor()
        
        print(f"Sistema ativo - Atualizações a cada {self.update_interval} segundos")
        print("Monitor de tempo ativo - Horários atualizados a cada minuto")
    
    def stop_monitoring(self):
        """Para o monitoramento"""
        print("Parando monitoramento...")
        self.running = False
        if self.file_observer:
            self.file_observer.stop()
    
    def setup_file_monitor(self):
        """Configura monitor para detectar mudanças no dashboard.json"""
        class ConfigChangeHandler(FileSystemEventHandler):
            def __init__(self, api_instance):
                self.api = api_instance
                
            def on_modified(self, event):
                if event.src_path.endswith('dashboard.json') and not event.is_directory:
                    # Usar threading para não bloquear o file watcher
                    threading.Thread(
                        target=self.api.handle_file_change, 
                        daemon=True
                    ).start()
        
        event_handler = ConfigChangeHandler(self)
        self.file_observer = Observer()
        self.file_observer.schedule(event_handler, path='.', recursive=False)
        self.file_observer.start()

def main():
    """Função principal"""
    dashboard_api = DashboardAPI()
    
    try:
        dashboard_api.start_monitoring()
        
        # Manter o programa rodando
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nEncerrando sistema...")
        dashboard_api.stop_monitoring()

if __name__ == "__main__":
    main()