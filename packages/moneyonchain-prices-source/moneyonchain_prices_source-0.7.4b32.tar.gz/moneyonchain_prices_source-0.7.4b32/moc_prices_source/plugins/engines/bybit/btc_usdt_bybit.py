from ...pairs.simple import BTC_USDT
from ...base import BaseWithFailover, Engines, Decimal



base_uri = "https://{}/v5/market/tickers?category=spot&symbol=BTCUSDT"

@Engines.register_decorator()
class Engine(BaseWithFailover):

    _description = "Bybit"
    _uri = base_uri.format("api.bybit.com")
    _uri_failover = base_uri.format("moc-proxy-api-bybit.moneyonchain.com")
    _coinpair = BTC_USDT
    _max_time_without_price_change = 600 # 10m, zero means infinity

    def _map(self, data):
        data = data['result']['list'][0]        
        return {
            'price': (Decimal(data['bid1Price']) +
                      Decimal(data['ask1Price'])) / Decimal('2')
        }
