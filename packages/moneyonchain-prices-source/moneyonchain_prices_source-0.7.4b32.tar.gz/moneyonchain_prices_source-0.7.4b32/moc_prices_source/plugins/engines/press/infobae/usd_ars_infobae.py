from ....pairs.simple import USD_ARS
from ....base import EngineWebScraping, Engines, Decimal 



to_dec = lambda x: Decimal(str(x).replace('.', '').replace(',', '.'))

@Engines.register_decorator()
class Engine(EngineWebScraping):

    _description = "Infobae"
    _uri = "https://www.infobae.com/economia/divisas/dolar-hoy/"
    _coinpair = USD_ARS
    _max_age = 3600 # 1hs.
    _max_time_without_price_change = 0 # zero means infinity

    def _scraping(self, html):
        value = None
        for s in html.find_all ('div', attrs={'class':'exchange-dolar-item'}):
            d = list(map(lambda x: x.strip(), s.strings))
            if len(d)==6 and d[0]=='Dólar blue':
                try:
                    value = value = to_dec(d[2])
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
