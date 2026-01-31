from ...pairs.simple import BTC_USD
from ...base import Base, Engines



@Engines.register_decorator()
class Engine(Base):

    _description = "Blockchain"
    _uri = "https://blockchain.info/ticker"
    _coinpair = BTC_USD

    def _map(self, data):
        return {
            'price':  data['USD']['last']
            }
