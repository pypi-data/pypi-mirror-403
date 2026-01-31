from ...pairs.simple import BTC_USDT
from ...base import Base, Engines



@Engines.register_decorator()
class Engine(Base):

    _description = "Coinbase"
    _uri = "https://api.coinbase.com/v2/exchange-rates?currency=BTC"
    _coinpair = BTC_USDT
    _max_time_without_price_change = 600 # 10m, zero means infinity

    def _map(self, data):
        return {
            'price':  data['data']['rates']['USDT']
            }
