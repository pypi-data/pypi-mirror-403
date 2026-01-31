from ...pairs.simple import BTC_ARS
from ...base import Base, Engines, Decimal



@Engines.register_decorator()
class Engine(Base):

    _description = "belo.app"
    _uri = "https://api.belo.app/public/price"
    _coinpair = BTC_ARS   
    _max_age = 3600 # 1hs.
    _max_time_without_price_change = 0    # zero means infinity

    def _map(self, data):
        value = {}
        for i in data:
            if i['pairCode']=='BTC/ARS':
                value['price'] = (Decimal(i['ask']) + Decimal(i['bid'])) / Decimal('2')
                break
        return value
