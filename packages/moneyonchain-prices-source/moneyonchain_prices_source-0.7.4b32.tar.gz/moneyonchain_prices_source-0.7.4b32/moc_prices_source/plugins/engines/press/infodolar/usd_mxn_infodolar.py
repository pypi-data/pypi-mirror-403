from ....pairs.simple import USD_MXN
from ....base import EngineWebScraping, Engines, Decimal



@Engines.register_decorator()
class Engine(EngineWebScraping):

    _description = "InfoDolar.com.mx"
    _uri = "https://www.infodolar.com.mx"
    _coinpair = USD_MXN
    _max_age = 3600 # 1hs.
    _max_time_without_price_change = 0 # zero means infinity


    def _scraping(self, html):
        value = None
        table = html.find('table', id="DolarPromedio")
        if table:
            values = []
            for s in table.find_all ('td', attrs={'class':'colCompraVenta'} ):
                d = list(map(lambda x: x.strip(), s.strings))[0].replace('$', '').replace(',', '.').strip()
                values.append(d)
            values = values[:2]
            if len(values)==2:
                try:
                    value = (Decimal(values[0]) + Decimal(values[1]))/Decimal(2) 
                except:
                    value = None

        if not value:
            self._error = "Response format error"
            return None
        return {
            'price':  value
        }
