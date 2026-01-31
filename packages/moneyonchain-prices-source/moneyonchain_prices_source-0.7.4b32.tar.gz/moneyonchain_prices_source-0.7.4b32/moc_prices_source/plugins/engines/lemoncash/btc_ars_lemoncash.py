from ...pairs.simple import BTC_ARS
from ...base import Base, Engines, Decimal



@Engines.register_decorator()
class Engine(Base):

    _description = "Lemoncash"
    _uri = "https://api.lemoncash.com.ar/api/v1/exchange-rates-quotations-external"
    _coinpair = BTC_ARS
    _max_age = 3600 # 1hs.
    _max_time_without_price_change = 0 # zero means infinity

    def _map(self, data):
        value = {}
        for i in data['results']:
            if i['instrument']=='BTC-ARS':
                value['price'] = (Decimal(i['purchase_price']['amount']) \
                                  + Decimal(i['sale_price']['amount'])) / Decimal('2')
                break       
        return value
