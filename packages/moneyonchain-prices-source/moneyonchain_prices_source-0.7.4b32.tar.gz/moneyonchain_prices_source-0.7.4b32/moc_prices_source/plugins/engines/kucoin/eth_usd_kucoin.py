from ...pairs.simple import ETH_USD
from ...base import Base, Engines



@Engines.register_decorator()
class Engine(Base):

    _description = "Kucoin"
    _uri = "https://api.kucoin.com/api/v1/market/stats?symbol=ETH-USDT"
    _coinpair = ETH_USD

    def _map(self, data):
        return {
            'price': data['data']['last'],
            'volume': data['data']['vol'] }
