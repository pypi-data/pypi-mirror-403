from ....pairs.simple import USD_ARS_CCL
from ....base import EngineWebScraping, Engines, Decimal



to_dec = lambda x: Decimal(str(x).replace('.', '').replace(',', '.'))

@Engines.register_decorator()
class Engine(EngineWebScraping):

    _description = "InfoDolar.com"
    _uri = "https://www.infodolar.com/cotizacion-dolar-contado-con-liquidacion.aspx"
    _coinpair = USD_ARS_CCL
    _max_age = 3600 # 1hs.
    _max_time_without_price_change = 0 # zero means infinity


    def _scraping(self, html):
        value = None
        table = html.find('table', id="CompraVenta")
        if table:
            values = []
            for s in table.find_all ('td', attrs={'class':'colCompraVenta'} ):
                d = to_dec(list(map(lambda x: x.strip(), s.strings))[0
                    ].replace('$', '').strip())
                values.append(d)
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
