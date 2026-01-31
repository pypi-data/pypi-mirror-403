from ...pairs.simple import BTC_ARS
from ...base import Base, Engines, Decimal



@Engines.register_decorator()
class Engine(Base):

    _description = "BuenBit"
    _uri = "http://91f83c67-4611-4562-ae66-421ac3d642eb.buenbit.com/public/market_price/btc/ars"
    _coinpair = BTC_ARS
    _max_age = 3600 # 1hs.
    _max_time_without_price_change = 0 # zero means infinity

    def _map(self, data):
        return {'price': Decimal(data['price'])}
