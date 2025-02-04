import requests
from decimal import Decimal
from django.conf import settings
import time
from django.core.cache import cache
from django.core.cache.backends.base import CacheKeyWarning
import warnings

class FinancialAPIService:
    def __init__(self):
        self.alpha_vantage_key = settings.ALPHA_VANTAGE_API_KEY
        self.news_api_key = settings.NEWS_API_KEY
        
    def _make_alpha_vantage_request(self, url):
        """Méthode helper pour gérer les requêtes Alpha Vantage avec cache"""
        try:
            cache_key = f"alpha_vantage_{hash(url)}"  # Utiliser un hash pour éviter les problèmes de caractères spéciaux
            cached_response = cache.get(cache_key)
            
            if cached_response:
                return cached_response
            
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            # Vérifier si l'API renvoie une erreur de limite
            if "Note" in data:
                return None
                
            # Mettre en cache pendant 5 minutes
            try:
                cache.set(cache_key, data, 300)
            except (CacheKeyWarning, Exception) as e:
                warnings.warn(f"Erreur de cache: {str(e)}")
                
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"Erreur de requête API: {str(e)}")
            return None
        except Exception as e:
            print(f"Erreur inattendue: {str(e)}")
            return None
    
    def get_stock_price(self, symbol):
        url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={self.alpha_vantage_key}'
        data = self._make_alpha_vantage_request(url)
        
        if data and 'Global Quote' in data:
            return data['Global Quote'].get('05. price')
        return None
    
    def get_financial_news(self):
        url = f'https://newsapi.org/v2/top-headlines?country=fr&category=business&apikey={self.news_api_key}'
        response = requests.get(url)
        return response.json()['articles'] if 'articles' in response.json() else []
    
    def get_crypto_prices(self):
        url = 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=eur'
        response = requests.get(url)
        return response.json()
    
    def get_savings_rates(self):
        # Simulation des taux d'épargne (à remplacer par une vraie API)
        return {
            'Livret A': '3.00%',
            'LDDS': '3.00%',
            'LEP': '5.00%',
            'PEL': '2.00%'
        }
    
    def get_top_stocks(self):
        """Récupère les meilleures actions à suivre avec gestion des erreurs"""
        symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'NVDA']
        stocks_data = []
        
        for symbol in symbols:
            url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={self.alpha_vantage_key}'
            data = self._make_alpha_vantage_request(url)
            
            if data and 'Global Quote' in data:
                quote = data['Global Quote']
                stocks_data.append({
                    'symbol': symbol,
                    'price': float(quote.get('05. price', 0)),
                    'change_percent': quote.get('10. change percent', '0%'),
                    'volume': quote.get('06. volume', '0'),
                })
            else:
                # Ajouter des données par défaut si l'API échoue
                stocks_data.append({
                    'symbol': symbol,
                    'price': 0.0,
                    'change_percent': '0%',
                    'volume': '0',
                })
            
            # Pause pour respecter les limites de l'API
            time.sleep(0.2)
        
        return stocks_data
    
    def get_market_indices(self):
        """Récupère les principaux indices boursiers avec gestion des erreurs"""
        indices = ['^FCHI', '^STOXX50E', '^GSPC']  # CAC 40, EURO STOXX 50, S&P 500
        indices_data = []
        
        for index in indices:
            url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={index}&apikey={self.alpha_vantage_key}'
            data = self._make_alpha_vantage_request(url)
            
            if data and 'Global Quote' in data:
                quote = data['Global Quote']
                indices_data.append({
                    'name': self._get_index_name(index),
                    'value': float(quote.get('05. price', 0)),
                    'change_percent': quote.get('10. change percent', '0%'),
                })
            else:
                # Ajouter des données par défaut si l'API échoue
                indices_data.append({
                    'name': self._get_index_name(index),
                    'value': 0.0,
                    'change_percent': '0%',
                })
            
            # Pause pour respecter les limites de l'API
            time.sleep(0.2)
        
        return indices_data
    
    def get_stock_details(self, symbol):
        """Récupère les détails d'une action spécifique"""
        url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={self.alpha_vantage_key}'
        data = self._make_alpha_vantage_request(url)
        
        if data:
            return {
                'name': data.get('Name', symbol),
                'sector': data.get('Sector', 'N/A'),
                'pe_ratio': data.get('PERatio', 'N/A'),
                'dividend_yield': data.get('DividendYield', 'N/A'),
                'market_cap': data.get('MarketCapitalization', 'N/A'),
            }
        return None
    
    def _get_index_name(self, symbol):
        index_names = {
            '^FCHI': 'CAC 40',
            '^STOXX50E': 'EURO STOXX 50',
            '^GSPC': 'S&P 500'
        }
        return index_names.get(symbol, symbol) 