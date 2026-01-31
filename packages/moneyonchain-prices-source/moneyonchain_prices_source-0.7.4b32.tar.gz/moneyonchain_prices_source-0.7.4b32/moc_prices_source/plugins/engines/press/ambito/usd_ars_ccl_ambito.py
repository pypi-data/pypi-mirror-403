from ....pairs.simple import USD_ARS_CCL
from ....base import Base, Engines, Decimal



@Engines.register_decorator()
class Engine(Base):

    _description = "Ambito.com"
    _uri = "https://mercados.ambito.com//dolarrava/cl/variacion"
    _coinpair = USD_ARS_CCL
    _max_age = 3600 # 1hs.
    _max_time_without_price_change = 0 # zero means infinity
    _headers = {'User-agent': 'Mozilla/5.0'} # FIX: 403 Client Error Forbidden

    def _map(self, data):
        values = [data['compra'], data['venta']]
        values = list(map(lambda x: Decimal(str(x).replace(',', '.')), values))
        value = sum(values)/len(values)
        return {
            'price':  value
        }
