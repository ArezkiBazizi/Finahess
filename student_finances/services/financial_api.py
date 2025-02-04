class FinancialAPIService:
    def __init__(self):
        pass
        
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