from ....pairs.simple import USD_ARS
from ....base import Base, Engines, Decimal 



@Engines.register_decorator()
class Engine(Base):

    _description = "CriptoYa.com"
    _uri = "https://criptoya.com/api/dolar"
    _coinpair = USD_ARS
    _max_age = 3600 # 1hs.
    _max_time_without_price_change = 0 # zero means infinity

    def _map(self, data):
        return {
            'price':  (Decimal(data['blue']['ask']) + 
                       Decimal(data['blue']['bid'])) / Decimal('2')
        }
