from ....pairs.simple import USD_ARS
from ....base import EngineWebScraping, Engines, Decimal 



@Engines.register_decorator()
class Engine(EngineWebScraping):

    _description = "DolarHoy.com"
    _uri = "https://dolarhoy.com/cotizaciondolarblue"
    _coinpair = USD_ARS
    _max_age = 10800 # 3hs.
    _max_time_without_price_change = 0 # zero means infinity


    def _scraping(self, html):
        value = None
        def str2dec(x):
            return Decimal(str(x).replace('$', '').replace(',', '.'))
        for s in html.find_all ('div', attrs={'class':'tile cotizacion_value'}):
            d = list(map(lambda x: x.strip().lower(), s.parent.strings))
            if len(d)==6 and d[0]=='dólar libre' and d[1]=='compra' and d[3]=='venta':
                try:
                    value = (str2dec(d[2]) + str2dec(d[4]))/Decimal(2) 
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
