import requests

METEOBLUE_KEY = "of3PKVjcdt4F0ixS"

# Cache simples para coordenadas (evitar requests repetidas)
coordinates_cache = {}

def get_coordinates(location):
    """
    Busca coordenadas usando OpenStreetMap Nominatim
    """
    if not location:
        return None
        
    # Verificar cache primeiro
    if location in coordinates_cache:
        #print(f"Coordenadas em cache para {location}")
        return coordinates_cache[location]
    
    headers = {
        "User-Agent": "Janks/1.0 (lfcfrontin@gmail.com)"
    }
    url = f"https://nominatim.openstreetmap.org/search?q={location}&format=json"
    
    try:
        #print(f"Buscando coordenadas para: {location}")
        response = requests.get(url, timeout=10, headers=headers)
        data = response.json()
        
        if data:
            lat = data[0]["lat"]
            lon = data[0]["lon"]
            
            # Salvar no cache
            coordinates_cache[location] = (lat, lon)
            #print(f"Coordenadas encontradas: {lat}, {lon}")
            return lat, lon
        else:
            #print(f"Nenhuma coordenada encontrada para: {location}")
            return None
            
    except requests.exceptions.RequestException as e:
        #print(f"Erro ao obter coordenadas: {str(e)}")
        return None

def get_weather_condition(pictocode, precipitation, precipitation_probability):
    """
    Converte os dados meteoblue em condições de clima mais descritivas
    """
    # Mapeamento baseado nos códigos pictocode do Meteoblue
    # Códigos comuns: 
    # 1-5: ensolarado/claro
    # 6-10: parcialmente nublado
    # 16-20: nublado
    # 22-33: nublado com possibilidade de chuva
    # 7, 19, 28: chuvoso
    
    if precipitation > 0.1 or precipitation_probability > 70:
        return "chuvoso"
    elif pictocode in [1, 2, 3, 4, 5]:
        return "ensolarado"
    elif pictocode in [6, 7, 8, 9, 10, 11, 12, 13, 14, 15]:
        return "nublado"
    elif pictocode in [16, 17, 18]:
        return "nublado"
    elif pictocode in [19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33]:
        if precipitation_probability > 50:
            return "chuvoso"
        else:
            return "nublado"
    else:
        # Fallback baseado apenas na precipitação
        if precipitation > 0.05:
            return "chuvoso"
        elif precipitation_probability > 30:
            return "nublado"
        else:
            return "ensolarado"

def get_weather(location):
    """
    Busca clima por localização com previsão detalhada
    """
    if not location:
        location = "Rio de Janeiro, Brasil"
        
    # Obter coordenadas
    coords = get_coordinates(location)
    if not coords:
        #print(f"Não foi possível obter coordenadas para {location}")
        return None
        
    lat, lon = coords
    
    # Buscar dados do clima
    url = f"https://my.meteoblue.com/packages/basic-1h?apikey={METEOBLUE_KEY}&lat={lat}&lon={lon}&asl=5&format=json"
    
    try:
        #print(f"Buscando clima para lat={lat}, lon={lon}")
        response = requests.get(url, timeout=10)
        data = response.json()
        ##print("data = ", data)
        
        # Dados atuais (primeira hora)
        temp = data["data_1h"]["temperature"][0]
        rain = data["data_1h"]["precipitation"][0]
        pictocode = data["data_1h"]["pictocode"][0]
        precipitation_prob = data["data_1h"]["precipitation_probability"][0]
        humidity = data["data_1h"]["relativehumidity"][0]
        date = data["metadata"]["modelrun_updatetime_utc"][0:10]
        time = data["metadata"]["modelrun_updatetime_utc"][11:16]
        time_zone = data["metadata"]["utc_timeoffset"]

        
        final_time = apply_timezone_offset(time, time_zone)

        
        # Determinar condição do clima
        condition = get_weather_condition(pictocode, rain, precipitation_prob)
        
        return {
            "temp": temp,
            "rain": rain > 0,
            "rain_mm": rain,
            "condition": condition,
            "precipitation_probability": precipitation_prob,
            "humidity": humidity,
            "pictocode": pictocode,
            "date": date,
            "time": final_time
        }
        
    except Exception as e:
        #print(f"Erro na previsão do tempo: {str(e)}")
        return None

def get_weather_forecast(location, hours=24):
    """
    Obtém previsão do tempo para as próximas horas
    """
    if not location:
        location = "Rio de Janeiro, Brasil"
        
    coords = get_coordinates(location)
    if not coords:
        #print(f"Não foi possível obter coordenadas para {location}")
        return None
        
    lat, lon = coords
    
    url = f"https://my.meteoblue.com/packages/basic-1h?apikey={METEOBLUE_KEY}&lat={lat}&lon={lon}&asl=5&format=json"
    
    try:
        #print(f"Buscando previsão para lat={lat}, lon={lon}")
        response = requests.get(url, timeout=10)
        data = response.json()
        
        forecast = []
        data_hours = min(hours, len(data["data_1h"]["temperature"]))
        
        for i in range(data_hours):
            temp = data["data_1h"]["temperature"][i]
            rain = data["data_1h"]["precipitation"][i]
            pictocode = data["data_1h"]["pictocode"][i]
            precipitation_prob = data["data_1h"]["precipitation_probability"][i]
            humidity = data["data_1h"]["relativehumidity"][i]
            time = data["data_1h"]["time"][i]
            
            condition = get_weather_condition(pictocode, rain, precipitation_prob)
            
            forecast.append({
                "temp": int(temp),
                "condition": condition,
            })
        
        return forecast
        
    except Exception as e:
        #print(f"Erro na previsão do tempo: {str(e)}")
        return None

def get_simple_weather(location):
    """
    Versão simplificada que retorna apenas a condição atual
    """
    weather = get_weather(location)
    if weather:
        return weather["condition"]
    return None


#Quero uma função que recee duas strings um no formato HH:MM e outra no tipo assim "-3.0" ou "3.0", quero que retorne no formato HH:MM com o fuso horário aplicado.
def apply_timezone_offset(time_str, offset_str):
    """
    Aplica um offset de fuso horário a uma string de hora no formato HH:MM.
    
    :param time_str: String no formato HH:MM
    :param offset_str: String representando o offset, como "-3.0" ou "3.0"
    :return: String no formato HH:MM com o fuso horário aplicado
    """
    from datetime import datetime, timedelta
    
    # Converter a string de hora para um objeto datetime
    time_obj = datetime.strptime(time_str, "%H:%M")
    
    # Converter o offset para horas e minutos
    offset_hours = float(offset_str)
    
    # Aplicar o offset
    adjusted_time = time_obj + timedelta(hours=offset_hours)
    
    # Retornar a hora ajustada no formato HH:MM
    return adjusted_time.strftime("%H:%M")


if __name__ == "__main__":
    location = "Rio de Janeiro, Brasil"
    print(get_weather(location))
# Exemplo de uso:
# location = "São Paulo, Brasil"
# #print(get_simple_weather(location))
# #print(get_weather(location))

    # #print(get_weather_forecast(location))
# #print(get_weather_forecast(location, hours=12))
# #print(get_weather_forecast(location, hours=48))
# #print(get_weather_forecast(location, hours=72))
# #print(get_weather_forecast(location, hours=168))  # Previsão semanal