import requests
import requests.auth
import json
import time
import os

class RedditHeadlineFetcher:
    def __init__(self):
        self.client_id = "xAj3eLdN2xYO0xQYv4AadA"
        self.client_secret = "PKGHQWftIb3tIhBLYBRtTbNIj9lbMw"  
        self.user_agent = "headline_fetcher/1.0 by Vinny_007"
        self.token_file = "reddit_token.json"
        self.access_token = None
        self.token_expiration = None
        
    def authenticate(self):
        if self._load_token():
            return True
            
        auth = requests.auth.HTTPBasicAuth(self.client_id, self.client_secret)
        data = {"grant_type": "client_credentials"}
        headers = {"User-Agent": self.user_agent}
        
        try:
            response = requests.post(
                "https://www.reddit.com/api/v1/access_token",
                auth=auth,
                data=data,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            token_data = response.json()
            #print(token_data)
            self._save_token(token_data)
            return True
        except Exception as e:
            print(f"Erro de autenticação: {str(e)}")
            return False
    
    def _save_token(self, token_data):
        """Salva o token com data de expiração"""
        self.access_token = token_data['access_token']
        self.token_expiration = time.time() + token_data['expires_in'] - 300
        
        with open(self.token_file, 'w') as f:
            json.dump({
                "access_token": self.access_token,
                "expiration": self.token_expiration
            }, f)
    
    def _load_token(self):
        """Carrega token salvo se ainda for válido"""
        if not os.path.exists(self.token_file):
            return False
            
        try:
            with open(self.token_file, 'r') as f:
                token_data = json.load(f)
                if token_data['expiration'] > time.time():
                    self.access_token = token_data['access_token']
                    self.token_expiration = token_data['expiration']
                    return True
        except:
            pass
        return False
    
    def get_headlines(self, subreddits, limit=7, time_filter='week'):
        """
        Busca as headlines mais populares de subreddits específicos
        Args:
            subreddits: Lista de subreddits (ex: ['python', 'technology'])
            limit: Número máximo de posts por subreddit
            time_filter: all, day, hour, month, week, year
        """
        if not self.authenticate():
            return None
            
        headers = {"Authorization": f"bearer {self.access_token}", "User-Agent": self.user_agent}
        params = {"limit": limit, "t": time_filter}
        
        all_headlines = []
        
        for sub in subreddits:
            try:
                response = requests.get(
                    f"https://oauth.reddit.com/r/{sub}/top",
                    headers=headers,
                    params=params,
                    timeout=15
                )
                response.raise_for_status()
                data = response.json()
                # print(data)  # Debug removido
                for post in data['data']['children']:
                    post_data = post['data']
                    all_headlines.append({
                        "title": post_data['title'],
                        "subreddit": post_data['subreddit'],
                        "score": post_data['score'],
                        "author": post_data['author'],
                        "created": time.strftime('%Y-%m-%d', time.localtime(post_data['created_utc'])),
                        "url": f"https://reddit.com{post_data['permalink']}",
                        "comments": post_data['num_comments']
                    })
                    
            except Exception as e:
                print(f"Erro em r/{sub}: {str(e)}")
        
        # Ordena por score (popularidade)
        return sorted(all_headlines, key=lambda x: x['score'], reverse=True)

def main():
    fetcher = RedditHeadlineFetcher()
    
    print("="*50)
    print("HEADLINE FETCHER - VINNY_007")
    print("="*50)
    
    # Configurar subreddits
    default_subs = ["technology", "programming", "science", "worldnews"]
    print(f"\nSubreddits padrão: {', '.join(default_subs)}")
    
    custom = input("\nDeseja usar subreddits personalizados? (s/n): ").lower()
    if custom == 's':
        subs_input = input("Digite subreddits (separados por vírgula): ")
        subreddits = [sub.strip() for sub in subs_input.split(",") if sub.strip()]
    else:
        subreddits = default_subs
    
    # Obter headlines
    print("\nBuscando as headlines mais populares...")
    headlines = fetcher.get_headlines(subreddits, limit=7)
    
    # Mostrar resultados
    if not headlines:
        print("\nNão foi possível obter headlines. Verifique sua conexão ou autenticação.")
        return
    
    print("\nHEADLINES MAIS POPULARES")
    print("="*80)
    for i, post in enumerate(headlines, 1):
        print(f"{i}. [{post['subreddit']}] {post['title']}")
        print(f"   {post['score']} | {post['comments']} | {post['author']} | {post['created']}")
        print(f"   {post['url']}")
        print("-"*80)

if __name__ == "__main__":
    main()