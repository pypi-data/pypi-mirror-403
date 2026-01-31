from ...pairs.simple import ETH_BTC
from ...base import Base, Engines



@Engines.register_decorator()
class Engine(Base):

    _description = "Bitfinex"
    _uri = "https://api-pub.bitfinex.com/v2/ticker/tETHBTC"
    _coinpair = ETH_BTC

    def _map(self, data):
        return {
            'price':  data[6],
            'volume': data[7]}
