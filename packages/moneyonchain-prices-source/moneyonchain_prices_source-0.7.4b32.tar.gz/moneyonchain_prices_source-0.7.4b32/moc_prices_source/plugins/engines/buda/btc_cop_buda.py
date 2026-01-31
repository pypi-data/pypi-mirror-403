from ...pairs.simple import BTC_COP
from ...base import Base, Engines, Decimal



@Engines.register_decorator()
class Engine(Base):

    _description = "buda.com"
    _uri = "https://www.buda.com/api/v2/markets/BTC-COP/ticker"
    _coinpair = BTC_COP
    _max_age = 3600 # 1hs.
    _max_time_without_price_change = 0 # zero means infinity

    def _map(self, data):
        return {
            'price': (Decimal(data['ticker']['min_ask'][0]) + Decimal(
                data['ticker']['max_bid'][0])) / Decimal('2'),
            'volume': data['ticker']['volume'][0]
        }
