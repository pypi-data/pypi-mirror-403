from ....pairs.simple import USD_ARS
from ....base import EngineWebScraping, Engines, Decimal 



to_dec = lambda x: Decimal(str(x).replace('.', '').replace(',', '.'))

@Engines.register_decorator()
class Engine(EngineWebScraping):

    _description = "Cronista.com"
    _uri = "https://www.cronista.com/MercadosOnline/moneda.html?id=ARSB"
    _coinpair = USD_ARS
    _max_age = 3600 # 1hs.
    _max_time_without_price_change = 0 # zero means infinity


    def _scraping(self, html):
        value = None
        for s in html.find_all ('table', id="market-scrll-1"):
            d = list(map(lambda x: x.strip(), s.strings))
            if len(d)==10 and d[0]=='DÓLAR BLUE' and d[1]=='Compra' and d[2]=='$' and d[4]=='Venta' and d[5]=='$':
                try:
                    value = (to_dec(d[3]) + to_dec(d[6]))/Decimal(2) 
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
