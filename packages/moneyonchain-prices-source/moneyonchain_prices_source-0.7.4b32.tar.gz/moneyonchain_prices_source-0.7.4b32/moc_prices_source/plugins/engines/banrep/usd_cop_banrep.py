from ...pairs.simple import USD_COP
from ...base import Base, Engines 



@Engines.register_decorator()
class Engine(Base):

    _description = "BanRep"
    _uri = "https://totoro.banrep.gov.co/estadisticas-economicas/rest/consultaDatosService/consultaMercadoCambiario"
    _coinpair = USD_COP

    def _map(self, data):
        return {'price': data[-1][1]}
