from ....pairs.simple import USD_MXN
from ....base import EngineWebScraping, Engines, Decimal
from json import loads as json_load


@Engines.register_decorator()
class Engine(EngineWebScraping):

    _description = "ElEconomista.es"
    _uri = "https://www.eleconomista.es/cruce/USDMXN"
    _coinpair = USD_MXN
    _max_age = 3600 # 1hs.
    _max_time_without_price_change = 0 # zero means infinity
    _headers = {'User-agent': 'Mozilla/5.0'} # FIX: 403 Client Error Forbidden

    def _scraping(self, html):
        value = None
        for s in html.find_all('script', type="application/ld+json" ):
            try:
                value = Decimal(json_load(s.string.strip()).get('price'))
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
