from ...pairs.simple import RIF_BTC
from ...base import Base, Engines



@Engines.register_decorator()
class Engine(Base):

    _description = "Coingecko"
    _uri = "https://api.coingecko.com/api/v3/simple/price?ids=rif-token&vs_currencies=btc&include_24hr_vol=true"
    _coinpair = RIF_BTC
    _max_time_without_price_change = 0 # zero means infinity

    def _map(self, data):
        return {"price": data["rif-token"]['btc'], "volume": data["rif-token"]['btc_24h_vol']}
