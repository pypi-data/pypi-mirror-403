from ...pairs.special import RIF_BTC_MP1P
from ...base import BaseWithFailover, Engines, Decimal
from .rif_btc_binance import Engine as RifBtcEngine



base_uri = "https://{}/api/v3/depth?symbol=RIFBTC"
factor = 0.01

@Engines.register_decorator()
class Engine(BaseWithFailover):

    _description = "Binance"
    _uri = base_uri.format("api.binance.com")
    _uri_failover = base_uri.format("moc-proxy-api-binance.moneyonchain.com")
    _coinpair= RIF_BTC_MP1P
    _max_time_without_price_change = 0 # zero means infinity


    def __call__(self):
        price_engine = RifBtcEngine()
        ok = price_engine()
        self._error = price_engine.error
        self.base_price = price_engine.price
        if ok:
            ok = BaseWithFailover.__call__(self)
        return ok


    def _map(self, data):

        value = Decimal(0)

        if 'bids' in data.keys() and 'asks' in data.keys():
            lv = []
            for t in ['asks', 'bids']:
                data[t].sort(reverse=(t=='bids'))
                v = Decimal('0')
                for p, q in data[t]:
                    p, q = Decimal(str(p)), Decimal(str(q))
                    d = abs((self.base_price / p) - Decimal('1'))
                    if d>=Decimal(str(factor)):
                        q = Decimal('1')
                    v += (q*p)
                    if d>=Decimal(str(factor)):
                        break
                lv.append(v)
            value = min(lv)

        return {
            'price':  value}
