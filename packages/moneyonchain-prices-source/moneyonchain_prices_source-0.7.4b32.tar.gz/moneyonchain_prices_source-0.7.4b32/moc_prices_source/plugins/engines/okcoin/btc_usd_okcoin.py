from ...pairs.simple import BTC_USD
from ...base import Base, Engines



@Engines.register_decorator()
class Engine(Base):

    _description = "OkCoin"
    _uri = "https://www.okcoin.com/api/spot/v3/instruments/BTC-USD/ticker"
    _coinpair = BTC_USD

    def _map(self, data):
        return {
            'price':  data['last'],
            }
