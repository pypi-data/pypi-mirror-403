from ....pairs.simple import USD_ARS_CCL
from ....base import Base, Engines, Decimal



@Engines.register_decorator()
class Engine(Base):

    _description = "LaNacion.com.ar"
    _uri = "https://api-contenidos.lanacion.com.ar/json/V3/economia/cotizacionblue/DCCL"
    _coinpair = USD_ARS_CCL
    _max_age = 3600 # 1hs.
    _max_time_without_price_change = 0 # zero means infinity

    def _map(self, data):
        values = [data['compra'], data['venta']]
        values = list(map(lambda x: Decimal(str(x).replace(',', '.')), values))
        value = sum(values)/len(values)
        return {
            'price':  value
        }
