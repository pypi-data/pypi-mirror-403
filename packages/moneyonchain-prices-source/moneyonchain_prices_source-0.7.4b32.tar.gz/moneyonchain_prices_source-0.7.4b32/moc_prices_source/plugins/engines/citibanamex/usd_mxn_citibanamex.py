from ...pairs.simple import USD_MXN
from ...base import Base, Engines, Decimal



@Engines.register_decorator()
class Engine(Base):

    _description = "CitiBanamex"
    _uri = "https://finanzasenlinea.infosel.com/banamex/WSFeedJSON/service.asmx/DivisasLast?callback="
    _coinpair = USD_MXN
    _max_age = 3600 # 1hs.
    _max_time_without_price_change = 0 # zero means infinity

    def _map(self, data):
        value = None
        for i in data:
            if i['cveInstrumento']=="MXNUS":
                values = [
                    i['ValorActualCompra'],
                    i['ValorActualVenta']
                ]
                values = list(map(lambda x: Decimal(str(x).replace(',', '.')), values))
                value = sum(values)/len(values)
                break
        return {
            'price':  value
        }
