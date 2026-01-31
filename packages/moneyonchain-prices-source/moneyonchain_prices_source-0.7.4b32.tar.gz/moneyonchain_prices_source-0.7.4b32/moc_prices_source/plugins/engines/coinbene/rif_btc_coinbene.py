from ...pairs.simple import RIF_BTC
from ...base import Base, Engines



@Engines.register_decorator()
class Engine(Base):

    _description = "Coinbene"
    _uri = "https://openapi-exchange.coinbene.com/api/exchange/v2/market/ticker/one?symbol=RIF%2FBTC"
    _coinpair = RIF_BTC
    _max_time_without_price_change = 0 # zero means infinity

    def _map(self, data):
        return {
            'price':  data['data']['latestPrice'],
            'volume': data['data']['volume24h'] }
