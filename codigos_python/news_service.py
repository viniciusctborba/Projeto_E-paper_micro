import requests

NEWSAPI_KEY = "7c745c005a044b409959473e68aecd67"

def get_global_news(tema):
    """
    Sua função original - busca notícias por tema
    """
    url = "https://newsapi.org/v2/everything"
    params = {
        'q': tema,
        'language': 'pt',
        'sortBy': 'relevancy',
        'apiKey': NEWSAPI_KEY
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        if data["status"] == "ok" and data["totalResults"] > 0:
            return [article["title"] for article in data["articles"][:7]]
        print("NewsAPI retornou 0 resultados")
        return None
    except Exception as e:
        print(f"Erro nas notícias: {str(e)}")
        return None

# Para teste
if __name__ == "__main__":
    print("=== Teste News Service ===")
    
    # Teste 1
    print("\n1. Testando tema 'tecnologia':")
    resultado = get_global_news("tecnologia")
    print(f"Resultado: {resultado}")
    
    # Teste 2
    print("\n2. Testando tema 'brasil':")
    resultado = get_global_news("brasil")
    print(f"Resultado: {resultado}")