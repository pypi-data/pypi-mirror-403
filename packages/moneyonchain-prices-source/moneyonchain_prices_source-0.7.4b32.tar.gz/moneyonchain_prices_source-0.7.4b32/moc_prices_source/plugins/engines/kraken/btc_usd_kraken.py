from ...pairs.simple import BTC_USD
from ...base import Base, Engines



@Engines.register_decorator()
class Engine(Base):

    _description = "Kraken"
    _uri = "https://api.kraken.com/0/public/Ticker?pair=XXBTZUSD"
    _coinpair = BTC_USD

    def _map(self, data):
        return {
            'price':  data['result']['XXBTZUSD']['c'][0],
            'volume': data['result']['XXBTZUSD']['v'][1] }
