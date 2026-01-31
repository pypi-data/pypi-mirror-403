from ...pairs.simple import ETH_BTC
from ...base import Base, Engines



@Engines.register_decorator()
class Engine(Base):

    _description = "Kraken"
    _uri = "https://api.kraken.com/0/public/Ticker?pair=ETHBTC"
    _coinpair = ETH_BTC

    def _map(self, data):
        return {
            'price': data['result']['XETHXXBT']['c'][0],
            'volume': data['result']['XETHXXBT']['v'][1] }
