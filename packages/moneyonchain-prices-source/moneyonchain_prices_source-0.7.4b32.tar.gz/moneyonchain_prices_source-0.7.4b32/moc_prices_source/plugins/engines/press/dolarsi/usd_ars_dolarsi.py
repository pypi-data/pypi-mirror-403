from ....pairs.simple import USD_ARS
from ....base import Base, Engines, Decimal 



@Engines.register_decorator()
class Engine(Base):

    _description = "DolarSi.com"
    _uri = "https://www.dolarsi.com/api/api.php?type=valoresprincipales"
    _coinpair = USD_ARS
    _max_age = 3600 # 1hs.
    _max_time_without_price_change = 0 # zero means infinity

    def _map(self, data):
        value = None
        for i in data:
            if 'casa' in i:
                i = i['casa']
                if 'compra' in i and 'venta' in i and 'nombre' in i and i['nombre']=="Dolar Blue":
                    values = [i['compra'], i['venta']]
                    values = list(map(lambda x: Decimal(str(x).replace('.', '').replace(',', '.')), values))
                    value = sum(values)/len(values)
                    break
        return {
            'price':  value
        }
