from ...pairs.simple import BTC_USD
from ...base import Base, Engines



@Engines.register_decorator()
class Engine(Base):

    _description = "Coinbase"
    _uri = "https://api.coinbase.com/v2/prices/spot?currency=USD"
    _coinpair = BTC_USD

    def _map(self, data):
        return {
            'price':  data['data']['amount']
            }
