from ...pairs.simple import BTC_ARS
from ...base import Base, Engines, Decimal



@Engines.register_decorator()
class Engine(Base):

    _description = "Decrypto"
    _uri = "https://api.decrypto.la/1.0/frontend/trading/data/prices"
    _coinpair = BTC_ARS
    _max_age = 3600 # 1hs.
    _max_time_without_price_change = 0 # zero means infinity

    _headers = {'User-agent': 'Mozilla/5.0'} # FIX: 403 Client Error Forbidden

    def _map(self, data):
        value = {}
        for i in data['data']:
            if i['currencyToken']['codigo']=='BTCARS':
                value['price'] = (Decimal(i['dca']) + Decimal(i['dcb'])) / Decimal('2')
                break
        return value
