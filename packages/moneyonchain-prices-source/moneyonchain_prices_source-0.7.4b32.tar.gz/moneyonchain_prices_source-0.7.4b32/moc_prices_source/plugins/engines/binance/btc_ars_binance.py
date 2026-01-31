from ...pairs.simple import BTC_ARS
from ...base import BaseWithFailover, Engines



base_uri = "https://{}/api/v3/ticker/24hr?symbol=BTCARS"

@Engines.register_decorator()
class Engine(BaseWithFailover):

    _description  = "Binance"
    _uri = base_uri.format("api.binance.com")
    _uri_failover = base_uri.format("moc-proxy-api-binance.moneyonchain.com")
    _coinpair = BTC_ARS
    _max_age = 3600 # 1hs.
    _max_time_without_price_change = 0 # zero means infinity

    def _map(self, data):
        return {
            'price':  data['lastPrice'],
            'volume': data['volume']}
