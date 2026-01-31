from ....pairs.simple import USD_MXN
from ....base import EngineWebScraping, Engines, Decimal



@Engines.register_decorator()
class Engine(EngineWebScraping):

    _description = "Currency.me.uk"
    _uri = "https://www.currency.me.uk/convert/usd/mxn"
    _coinpair = USD_MXN
    _max_age = 3600 # 1hs.
    _max_time_without_price_change = 0 # zero means infinity

    def _scraping(self, html):
        value = None
        for s in html.find_all ('span', attrs={'class':'mini ccyrate'}):
            d = s.string.strip().split()
            if len(d)==5 and d[0]=="1" and d[1]=="USD" and d[2]=="=" and d[4]=="MXN":
                try:
                    value = Decimal(d[3])
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
