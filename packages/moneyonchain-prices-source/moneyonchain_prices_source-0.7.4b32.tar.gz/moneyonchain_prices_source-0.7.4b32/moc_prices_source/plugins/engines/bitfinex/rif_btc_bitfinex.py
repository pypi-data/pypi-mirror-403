from ...pairs.simple import RIF_BTC
from ...base import Base, Engines



@Engines.register_decorator()
class Engine(Base):

    _description = "Bitfinex"
    _uri = "https://api-pub.bitfinex.com/v2/ticker/tRIFBTC"
    _coinpair = RIF_BTC
    _max_time_without_price_change = 0 # zero means infinity

    def _map(self, data):
        return {
            'price':  data[6],
            'volume': data[7]}
