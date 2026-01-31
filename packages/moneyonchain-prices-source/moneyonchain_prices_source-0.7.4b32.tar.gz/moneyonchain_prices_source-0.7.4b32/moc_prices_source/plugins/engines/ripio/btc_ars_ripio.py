from ...pairs.simple import BTC_ARS
from ...base import Base, Engines, Decimal



@Engines.register_decorator()
class Engine(Base):

    _description = "Ripio"
    _uri = "https://app.ripio.com/api/v3/public/rates"
    _coinpair = BTC_ARS
    _max_age = 3600 # 1hs.
    _max_time_without_price_change = 0 # zero means infinity

    def _map(self, data):
        value = {}
        for i in data:
            if i['ticker']=='BTC_ARS':
                value['price'] = (Decimal(i['buy_rate']) + Decimal(
                    i['sell_rate'])) / Decimal('2')
                break
        return value
