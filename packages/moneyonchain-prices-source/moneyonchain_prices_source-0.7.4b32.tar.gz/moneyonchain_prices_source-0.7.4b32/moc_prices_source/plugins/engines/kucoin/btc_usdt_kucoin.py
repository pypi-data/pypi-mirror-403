from ...pairs.simple import BTC_USDT
from ...base import Base, Engines, Decimal



@Engines.register_decorator()
class Engine(Base):

    _description = "KuCoin"
    _uri = "https://api.kucoin.com/api/v1/market/orderbook/level1?symbol=BTC-USDT"
    _coinpair = BTC_USDT
    _max_time_without_price_change = 600 # 10m, zero means infinity

    def _map(self, data):
        data = data['data']        
        return {
            'price': (Decimal(data['bestAsk']) +
                      Decimal(data['bestBid'])) / Decimal('2')
        }
