from ...pairs.simple import BTC_COP
from ...base import Base, Engines, Decimal



@Engines.register_decorator()
class Engine(Base):

    _description = "bitso.com"
    _uri = "https://api.bitso.com/v3/ticker/?book=btc_cop"
    _coinpair = BTC_COP
    _max_age = 3600 # 1hs.
    _max_time_without_price_change = 0 # zero means infinity

    def _map(self, data):
        return {
            'price': (Decimal(data['payload']['ask']) + Decimal(
                data['payload']['bid'])) / Decimal('2'),
            'volume': data['payload']['volume']
        }
