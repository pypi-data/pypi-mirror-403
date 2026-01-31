from ....pairs.simple import USD_MXN
from ....base import Base, Engines



@Engines.register_decorator()
class Engine(Base):

    _description = "CoinMonitor.info"
    _uri = "https://mx.coinmonitor.info/data_ar_chart_DOLAR.json"
    _coinpair = USD_MXN
    _max_age = 3600 # 1hs.
    _max_time_without_price_change = 0 # zero means infinity

    # I couldn't get it to work without this
    _ssl_verify = False
    # I allways get this error: 
    #     File: '/path/to/moc_prices_source/engines/mxn_usd_coinmonitor.py', Ok!
    #     CoinMonitor.info MXN/USD
    #     HTTPSConnectionPool(host='mx.coinmonitor.info', port=443): Max retries
    #     exceeded with url: /data_ar_chart_DOLAR.json (Caused by
    #     SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED]
    #     certificate verify failed: unable to get local issuer certificate (_ssl.c:1131)')))
    # I leave this to solve it in another time

    def _map(self, data):
        return {
            'price':  data[0][1]
        }
