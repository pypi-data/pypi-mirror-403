from ....pairs.simple import USD_ARS_CCL
from ....base import Base, Engines



@Engines.register_decorator()
class Engine(Base):

    _description = "CriptoYa.com"
    _uri = "https://criptoya.com/api/dolar"
    _coinpair = USD_ARS_CCL
    _max_age = 3600 # 1hs.
    _max_time_without_price_change = 0 # zero means infinity

    def _map(self, data):
        prices = [ x['ci']['price'] for x in data['ccl'].values() ]
        return {
            'price':  sum(prices)/len(prices)
        }
