from ...pairs.simple import BTC_USDT
from ...base import Base, Engines



@Engines.register_decorator()
class Engine(Base):

    _description = "Bitfinex"
    _uri = "https://api-pub.bitfinex.com/v2/ticker/tBTCUST"
    _coinpair = BTC_USDT
    _max_time_without_price_change = 600 # 10m, zero means infinity

    def _map(self, data):
        return {
            'price':  data[6],
            'volume': data[7]}
