from ...pairs.simple import BTC_COP
from ...base import Base, Engines



@Engines.register_decorator()
class Engine(Base):

    _description = "Coinbase"
    _uri = "https://api.coinbase.com/v2/prices/BTC-COP/spot"
    _coinpair = BTC_COP

    def _map(self, data):
        return {
            'price':  data['data']['amount']
            }
