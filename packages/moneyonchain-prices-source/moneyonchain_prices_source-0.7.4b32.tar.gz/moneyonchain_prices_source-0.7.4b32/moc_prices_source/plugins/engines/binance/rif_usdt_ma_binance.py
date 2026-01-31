from typing import Dict, List, Any, Optional
from ...pairs.simple import RIF_USDT_MA
from ...base import Decimal, BaseWithFailover, Engines, envs



# Some params
base_uri = "https://{}/api/v3/depth?symbol=RIFUSDT"
max_quantity = Decimal(envs('MA_MAX_QUANTITY', 100000, int))
allow_degraded = envs('MA_ALLOW_DEGRADED', False, bool)

@Engines.register_decorator()
class Engine(BaseWithFailover):

    _description = "Binance"
    _uri = base_uri.format("api.binance.com")
    _uri_failover = base_uri.format("moc-proxy-api-binance.moneyonchain.com")
    _coinpair = RIF_USDT_MA
    _max_quantity = max_quantity
    _allow_degraded = allow_degraded
    _max_time_without_price_change = 0 # zero means infinity


    def _map(self, data: Dict[str, List[List[Any]]]
             ) -> Dict[str, Optional[Decimal]]:
        """
        Compute WDAP up to self._max_quantity on both sides of the order book.

        Expected input:
            data = {
                "asks": [[price, qty], ...],  # best ask (unsorted)
                "bids": [[price, qty], ...],  # best bid (unsorted)
            }
        
        Reference in `docs/fundamentals/wdap.md`
        """
        types_ = ['asks', 'bids']
        if all(map(lambda t: isinstance(data.get(t), list
                                        ) and data.get(t), types_)):
            total = Decimal('0')
            values = []
            max_quantity = self._max_quantity
            for type_ in types_:
                data[type_].sort(reverse=(type_=='bids'))
                spent, accumulated = Decimal('0'), Decimal('0')
                for x in data[type_]:
                    price, quantity = list(map(Decimal, x))
                    if (accumulated + quantity) >= max_quantity:
                        quantity = max_quantity - accumulated
                    accumulated += quantity
                    if accumulated >= max_quantity:
                        break               
                if accumulated<max_quantity:
                    max_quantity=accumulated
            for type_ in types_:
                spent, accumulated = Decimal('0'), Decimal('0')
                for x in data[type_]:
                    price, quantity = list(map(Decimal, x))
                    if (accumulated + quantity) >= max_quantity:
                        quantity = max_quantity - accumulated
                    spent += price * quantity
                    accumulated += quantity
                    if accumulated >= max_quantity:
                        break               
                total += accumulated
                values.append(spent * accumulated)
            degraded = bool(max_quantity<self._max_quantity)
            if self._allow_degraded or not(degraded):
                return {'price': (sum(values)/total)/max_quantity}
