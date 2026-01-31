from ...pairs.simple import BTC_ARS
from ...base import Base, Engines



@Engines.register_decorator()
class Engine(Base):

    _description = "satoshitango.com"
    _uri = "https://api.satoshitango.com/v3/ticker/ARS/BTC"
    _coinpair = BTC_ARS
    _max_age = 3600 # 1hs.
    _max_time_without_price_change = 0 # zero means infinity

    def _map(self, data):
        return {
            'price': data['data']['ticker']['BTC']['bid'],
            'volume': data['data']['ticker']['BTC']['volume']
        }
