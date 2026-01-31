from ....pairs.simple import USD_MXN
from ....base import EngineWebScraping, Engines, Decimal



@Engines.register_decorator()
class Engine(EngineWebScraping):

    _description = "X-rates.com"
    _uri = "https://www.x-rates.com/calculator/?from=USD&to=MXN&amount=1"
    _coinpair = USD_MXN
    _max_age = 3600 # 1hs.
    _max_time_without_price_change = 0 # zero means infinity

    def _scraping(self, html):
        value = None
        for s in html.find_all ('span', attrs={'class':'ccOutputTxt'}):
            d = list(filter(bool, map(lambda x: x.strip(), s.parent.strings)))
            if len(d)==4 and d[0]=="1.00 USD =" and d[3]=="MXN":
                try:
                    value = Decimal(''.join(d[1:3]))
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
