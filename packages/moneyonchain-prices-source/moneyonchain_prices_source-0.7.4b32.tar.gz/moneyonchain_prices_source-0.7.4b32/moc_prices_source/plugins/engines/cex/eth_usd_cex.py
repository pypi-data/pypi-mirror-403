from ...pairs.simple import ETH_USD
from ...base import Base, Engines



@Engines.register_decorator()
class Engine(Base):

    _description = "Cex"
    _uri = "https://cex.io/api/ticker/ETH/USD"
    _coinpair = ETH_USD

    def _map(self, data):
        return {
            'price': data['last'],
            'volume': data['volume'] }
