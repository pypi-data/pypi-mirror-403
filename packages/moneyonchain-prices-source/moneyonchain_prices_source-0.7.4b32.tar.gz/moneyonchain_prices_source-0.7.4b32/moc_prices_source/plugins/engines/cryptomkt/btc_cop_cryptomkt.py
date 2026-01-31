from ...pairs.simple import BTC_COP
from ...base import Base, Engines, Decimal, NoLiquidity



@Engines.register_decorator()
class Engine(Base):

    _description = "cryptomkt.com"
    _uri = "https://api.exchange.cryptomkt.com/api/3/public/ticker/BTCCOP"
    _coinpair = BTC_COP
    _max_age = 3600 # 1hs.
    _max_time_without_price_change = 0 # zero means infinity

    def _map(self, data):
        ask, bid = data['ask'], data['bid']
        if ask is None or bid is None:
            raise NoLiquidity()
        return {
            'price': (Decimal(ask) + Decimal(bid)) / Decimal('2'),
            'volume': data['volume']
        }
