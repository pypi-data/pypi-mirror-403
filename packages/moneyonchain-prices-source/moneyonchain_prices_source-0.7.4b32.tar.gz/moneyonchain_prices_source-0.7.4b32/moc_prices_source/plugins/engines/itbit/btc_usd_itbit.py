from ...pairs.simple import BTC_USD
from ...base import Base, Engines



@Engines.register_decorator()
class Engine(Base):

    _description = "ItBit"
    _uri = "https://api.itbit.com/v1/markets/XBTUSD/ticker"
    _coinpair  = BTC_USD

    def _map(self, data):
        return {
            'price':  data['lastPrice'],
            }
