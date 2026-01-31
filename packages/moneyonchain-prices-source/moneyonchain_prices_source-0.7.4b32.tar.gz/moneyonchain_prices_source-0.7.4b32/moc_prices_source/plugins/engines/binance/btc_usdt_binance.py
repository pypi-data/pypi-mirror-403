from ...pairs.simple import BTC_USDT
from ...base import BaseWithFailover, Engines, Decimal



base_uri = "https://{}/api/v3/ticker/bookTicker?symbol=BTCUSDT"

@Engines.register_decorator()
class Engine(BaseWithFailover):

    _description = "Binance"
    _uri = base_uri.format("api.binance.com")
    _uri_failover = base_uri.format("moc-proxy-api-binance.moneyonchain.com")
    _coinpair = BTC_USDT
    _max_time_without_price_change = 600 # 10m, zero means infinity

    def _map(self, data):
        return {
            'price': (Decimal(data['askPrice']) +
                      Decimal(data['bidPrice'])) / Decimal('2')
        }
