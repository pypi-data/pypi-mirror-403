from ...pairs.simple import BTC_USD
from ...base import Base, Engines



@Engines.register_decorator()
class Engine(Base):

    _description = "Bitfinex"
    _uri = "https://api-pub.bitfinex.com/v2/ticker/tBTCUSD"
    _coinpair = BTC_USD

    def _map(self, data):
        return {
            'price':  data[6],
            'volume': data[7]}
