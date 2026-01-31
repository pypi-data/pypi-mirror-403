from ...pairs.simple import USDT_USD
from ...base import Base, Engines, Decimal



@Engines.register_decorator()
class Engine(Base):

    _description = "Kraken"
    _uri = "https://api.kraken.com/0/public/Ticker?pair=USDTUSD"
    _coinpair = USDT_USD
    _max_time_without_price_change = 3600 # 1h, zero means infinity

    def _map(self, data):
        keys = list(data['result'].keys())
        if 1==len(keys):
            return {
                'price': (Decimal(data['result'][keys[0]]['a'][0]) +
                          Decimal(data['result'][keys[0]]['b'][0])
                          ) / Decimal('2'),
                'volume': data['result'][keys[0]]['v'][1] }
