from ....pairs.simple import USD_ARS_CCL
from ....base import Base, Engines



@Engines.register_decorator()
class Engine(Base):

    _description = "CoinMonitor.info"
    _uri = "https://coinmonitor.info/chart_DOLARES_24hs.json"
    _coinpair = USD_ARS_CCL
    _max_age = 3600 # 1hs.
    _max_time_without_price_change = 0 # zero means infinity

    def _map(self, data):
        return {
            'price':  data[0][3]
        }
