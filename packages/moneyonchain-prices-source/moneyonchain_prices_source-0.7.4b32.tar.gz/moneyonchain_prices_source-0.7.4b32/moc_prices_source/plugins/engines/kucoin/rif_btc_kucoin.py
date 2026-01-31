from ...pairs.simple import RIF_BTC
from ...base import Base, Engines



@Engines.register_decorator()
class Engine(Base):

    _description = "Kucoin"
    _uri = "https://openapi-v2.kucoin.com/api/v1/market/orderbook/level1?symbol=RIF-BTC"
    _coinpair = RIF_BTC
    _max_time_without_price_change = 0 # zero means infinity

    def _map(self, data):
        return {
            'price':  data['data']['price'],
            'volume': data['data']['size'] }
