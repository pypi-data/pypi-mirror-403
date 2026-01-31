from ...pairs.simple import BTC_USD
from ...base import Base, Engines



@Engines.register_decorator()
class Engine(Base):

    _description = "BitGO"
    _uri = "https://www.bitgo.com/api/v1/market/latest"
    _coinpair = BTC_USD

    def _map(self, data):
        return {
            'price':  data['latest']['currencies']['USD']['last'],
            'volume': data['latest']['currencies']['USD']['total_vol'],
            'timestamp': self._utcfromtimestamp(data[
                'latest']['currencies']['USD']['timestamp']) }
