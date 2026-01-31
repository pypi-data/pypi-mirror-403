from ...pairs.simple import BTC_USD
from ...base import Base, Engines



@Engines.register_decorator()
class Engine(Base):

    _description = "Bitstamp"
    _uri = "https://www.bitstamp.net/api/v2/ticker/btcusd/"
    _coinpair = BTC_USD

    def _map(self, data):
        return {
            'price':  data['last'],
            'volume': data['volume']}
