from ....pairs.simple import USD_MXN
from ....base import EngineWebScraping, Engines, Decimal



@Engines.register_decorator()
class Engine(EngineWebScraping):

    _description = "TheMoneyConverter.com"
    _uri = "https://themoneyconverter.com/USD/MXN"
    _coinpair = USD_MXN
    _max_age = 3600 # 1hs.
    _max_time_without_price_change = 0 # zero means infinity

    def _scraping(self, html):
        value = None
        for s in html.find_all ('span'):
            d = s.string.strip().split()
            if len(d)==3 and d[0]=="MXN/USD" and d[1]=="=":
                try:
                    value = Decimal(d[2])
                except:
                    value = None
                if value:
                    break
        if not value:
            self._error = "Response format error"
            return None
        return {
            'price':  value
        }
