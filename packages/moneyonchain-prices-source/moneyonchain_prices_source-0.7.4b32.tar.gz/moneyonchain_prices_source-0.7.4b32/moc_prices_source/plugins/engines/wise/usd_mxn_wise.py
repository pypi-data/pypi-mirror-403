from ...pairs.simple import USD_MXN
from ...base import Base, Engines, Decimal



@Engines.register_decorator()
class Engine(Base):

    _description = "Wise.com"
    _uri = "https://wise.com/rates/history+live?source=USD&target=MXN&length=1&resolution=hourly&unit=day"
    _coinpair = USD_MXN
    _max_age = 3600 # 1hs.
    _max_time_without_price_change = 0 # zero means infinity

    def _map(self, data):
        try:
            value = Decimal(str(data[-1]['value']))
        except:
            value = None        
        return {
            'price':  value
        }
