import paho.mqtt.client as mqtt
import json
import os
import time
import ssl # Importe ssl para suporte a TLS/SSL

# --- Configurações do Broker MQTT ---
MQTT_BROKER = "mqtt.janks.dev.br"
MQTT_PORT = 8883 # Porta 8883 geralmente indica MQTT com TLS/SSL
MQTT_USER = "aula"
MQTT_PASSWORD = "zowmad-tavQez"
MQTT_CLIENT_ID = "dashboard_client_python__"  # ID único do cliente
MQTT_TOPIC_PUBLISH = "dashboard" # Tópico para PUBLICAÇÃO
MQTT_TOPIC_SUBSCRIBE = "le_dashboard"          # NOVO: Tópico para SUBSCRIBE (ESP32 pode publicar aqui)

mqtt_client = None
mqtt_connected = False
# Variável para armazenar a callback de mensagem para a interface Tkinter
message_callback_ui = None

def set_message_callback_ui(callback_function):
    """
    Define uma função de callback a ser chamada quando uma mensagem MQTT é recebida.
    Isso permite que a UI Tkinter processe as mensagens.
    """
    global message_callback_ui
    message_callback_ui = callback_function

def on_connect(client, userdata, flags, rc):
    global mqtt_connected
    if rc == 0:
        print("[MQTT] Conectado ao broker MQTT com sucesso!")
        mqtt_connected = True
        # Se conectou, agora se inscreva no tópico de status
        client.subscribe(MQTT_TOPIC_SUBSCRIBE)
        print(f"[MQTT] Inscrito no tópico: {MQTT_TOPIC_SUBSCRIBE}")
    else:
        print(f"[MQTT] Falha na conexão, código de retorno: {rc}")
        mqtt_connected = False

def on_disconnect(client, userdata, rc):
    global mqtt_connected
    print(f"[MQTT] Desconectado do broker MQTT com código: {rc}")
    mqtt_connected = False

def on_message(client, userdata, msg):
    """
    Callback chamada quando uma mensagem é recebida no tópico subscrito.
    """
    print(f"[MQTT Mensagem Recebida] Tópico: {msg.topic}, Payload: {msg.payload.decode()}")
    # Se uma callback para a UI foi definida, chame-a
    if message_callback_ui:
        message_callback_ui(msg.topic, msg.payload.decode())

def connect_mqtt():
    global mqtt_client
    if mqtt_client and mqtt_client.is_connected():
        print("[MQTT] Já conectado.")
        return True

    # Cria o cliente MQTT com ID específico
    mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_ID, clean_session=True)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_disconnect = on_disconnect
    mqtt_client.on_message = on_message # Define a função de callback de mensagem

    if MQTT_USER and MQTT_PASSWORD:
        mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)

    # Configuração TLS/SSL (para porta 8883)
    # Você pode precisar especificar caminhos para CA certs, client certs e private keys
    # Se o broker usar certificados autoassinados ou não confiáveis,
    # ou se você precisar de autenticação mútua.
    try:
        # Por padrão, use TLS v1.2 e verifique o certificado do servidor.
        # Se seu broker usa um certificado autoassinado ou não tem um certificado válido,
        # você pode precisar de: cert_reqs=ssl.CERT_NONE (NÃO RECOMENDADO EM PRODUÇÃO!)
        mqtt_client.tls_set(tls_version=ssl.PROTOCOL_TLSv1_2)
        # Se você tiver um CA certificate para o broker, adicione:
        # mqtt_client.tls_set(ca_certs="path/to/ca.crt", tls_version=ssl.PROTOCOL_TLSv1_2)
        # Se o cliente precisar de um certificado e chave:
        # mqtt_client.tls_set(ca_certs="path/to/ca.crt", certfile="path/to/client.crt", keyfile="path/to/client.key", tls_version=ssl.PROTOCOL_TLSv1_2)

    except Exception as e:
        print(f"[MQTT] Erro ao configurar TLS: {e}. Verifique a porta e as configurações de certificado.")
        return False


    try:
        print(f"[MQTT] Tentando conectar a {MQTT_BROKER}:{MQTT_PORT} com Client ID: {MQTT_CLIENT_ID}...")
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
        for _ in range(5):
            if mqtt_connected:
                return True
            time.sleep(1)
        print("[MQTT] Tempo esgotado para conectar.")
        return False
    except Exception as e:
        print(f"[MQTT] Erro ao conectar ao broker: {e}. Certifique-se de que o broker está acessível e a porta/TLS estão corretos.")
        return False

def disconnect_mqtt():
    global mqtt_client
    if mqtt_client:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        print("[MQTT] Cliente MQTT desconectado.")

def send_layout_to_esp32(file_path="layout.json"):
    if not mqtt_connected:
        print("[ERRO] Cliente MQTT não conectado. Por favor, conecte antes de enviar.")
        return False

    if not os.path.exists(file_path):
        print(f"[ERRO] Arquivo de layout não encontrado para envio: {file_path}")
        return False

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        json_payload = json.dumps(config_data)
        print(f"\n[MQTT] Publicando no tópico '{MQTT_TOPIC_PUBLISH}':")
        # print(json_payload)  # Removido conforme solicitado

        info = mqtt_client.publish(MQTT_TOPIC_PUBLISH, json_payload, qos=1)
        info.wait_for_publish()
        print(f"[MQTT] Mensagem publicada com sucesso! ID: {info.mid}")
        return True
    except json.JSONDecodeError:
        print(f"[ERRO] Erro ao decodificar JSON do arquivo: {file_path}. Verifique a sintaxe.")
        return False
    except Exception as e:
        print(f"[ERRO] Ocorreu um erro ao enviar o layout: {e}")
        return False

def get_mqtt_client_status():
    global mqtt_connected
    return mqtt_connected