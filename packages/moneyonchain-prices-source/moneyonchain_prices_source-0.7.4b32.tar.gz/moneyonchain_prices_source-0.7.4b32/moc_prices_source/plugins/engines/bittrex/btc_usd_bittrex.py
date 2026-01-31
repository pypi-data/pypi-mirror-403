from ...pairs.simple import BTC_USD
from ...base import Base, Engines



@Engines.register_decorator()
class Engine(Base):

    _description = "Bittrex"
    _uri = "https://api.bittrex.com/api/v1.1/public/getticker?market=USD-BTC"
    _coinpair = BTC_USD

    def _map(self, data):
        return {
            'price':  data['result']['Last'],
            }
