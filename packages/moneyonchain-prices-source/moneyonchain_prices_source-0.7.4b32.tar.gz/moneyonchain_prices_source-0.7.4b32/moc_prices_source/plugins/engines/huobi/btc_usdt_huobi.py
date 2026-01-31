from ...pairs.simple import BTC_USDT
from ...base import Base, Engines, Decimal



@Engines.register_decorator()
class Engine(Base):

    _description = "Huobi"
    _uri = "https://api.huobi.pro/market/detail/merged?symbol=btcusdt"
    _coinpair = BTC_USDT
    _max_time_without_price_change = 600 # 10m, zero means infinity

    def _map(self, data):
        data = data['tick']     
        return {
            'price': (Decimal(data['bid'][0]) +
                      Decimal(data['ask'][0])) / Decimal('2')
        }
