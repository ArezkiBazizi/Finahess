import requests
from django.conf import settings

class FinancialAPIService:
    def __init__(self):
        self.alpha_vantage_key = settings.ALPHA_VANTAGE_API_KEY
        self.coingecko_url = "https://api.coingecko.com/api/v3"

    def get_crypto_data(self):
        """Récupère les données des cryptomonnaies"""
        try:
            response = requests.get(f"{self.coingecko_url}/coins/markets", params={
                'vs_currency': 'eur',
                'order': 'market_cap_desc',
                'per_page': 10,
                'page': 1,
                'sparkline': False
            })
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la récupération des données de cryptomonnaies: {str(e)}")
            return []

    def get_stock_data(self, symbol):
        """Récupère les données d'une action spécifique"""
        url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={self.alpha_vantage_key}'
        response = requests.get(url)
        data = response.json()
        return data.get('Global Quote', {})

    def get_market_data(self):
        """Récupère les données de marché"""
        # Pour l'instant, retourne des données fictives
        return {
            'indices': [
                {
                    'name': 'CAC 40',
                    'value': 7500.0,
                    'change_percent': '+0.5%'
                },
                {
                    'name': 'S&P 500',
                    'value': 4800.0,
                    'change_percent': '+0.3%'
                }
            ],
            'stocks': [
                {
                    'symbol': 'AAPL',
                    'price': 180.0,
                    'change_percent': '+1.2%'
                },
                {
                    'symbol': 'MSFT',
                    'price': 350.0,
                    'change_percent': '+0.8%'
                }
            ]
        } 