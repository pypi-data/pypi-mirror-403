from ...pairs.simple import BTC_USDT
from ...base import Base, Engines, Decimal



@Engines.register_decorator()
class Engine(Base):

    _description = "OKX"
    _uri = "https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT"
    _coinpair = BTC_USDT
    _max_time_without_price_change = 600 # 10m, zero means infinity

    def _map(self, data):
        data = data['data'][0]        
        return {
            'price': (Decimal(data['askPx']) +
                      Decimal(data['bidPx'])) / Decimal('2')
        }
