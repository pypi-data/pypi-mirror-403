from ...pairs.simple import ETH_USD
from ...base import Base, Engines



@Engines.register_decorator()
class Engine(Base):

    _description = "Gemini"
    _uri = "https://api.gemini.com/v1/pubticker/ETHUSD"
    _coinpair = ETH_USD

    def _map(self, data):
        return {
            'price': data['last'],
            }
