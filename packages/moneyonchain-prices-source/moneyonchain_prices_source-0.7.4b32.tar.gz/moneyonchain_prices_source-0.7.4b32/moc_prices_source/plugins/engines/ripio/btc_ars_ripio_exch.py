from ...pairs.simple import BTC_ARS
from ...base import Base, Engines, Decimal



@Engines.register_decorator()
class Engine(Base):

    _description = "Ripio exchange"
    _uri = "https://api.ripiotrade.co/v4/public/tickers/BTC_ARS"
    _coinpair = BTC_ARS
    _max_age = 3600 # 1hs.
    _max_time_without_price_change = 0 # zero means infinity

    def _map(self, data):
        return {
            'price': (Decimal(data['data']['ask']) + Decimal(data['data']['bid'])) / Decimal('2'),
            'volume': data['data']['volume']
        }
