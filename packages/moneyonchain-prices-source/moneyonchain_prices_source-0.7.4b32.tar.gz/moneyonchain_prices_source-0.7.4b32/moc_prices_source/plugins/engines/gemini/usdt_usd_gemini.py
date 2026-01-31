from ...pairs.simple import USDT_USD
from ...base import Base, Engines, Decimal



@Engines.register_decorator()
class Engine(Base):

    _description = "Gemini"
    _uri = "https://api.gemini.com/v1/pubticker/usdtusd"
    _coinpair = USDT_USD
    _max_time_without_price_change = 3600 # 1h, zero means infinity

    def _map(self, data):
        return {
            'price': (Decimal(data['ask']) + Decimal(data['bid'])) / Decimal('2'),
            }
