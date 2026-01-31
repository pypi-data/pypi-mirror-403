from ...pairs.simple import RIF_BTC
from ...base import BaseOnChain, Engines, EVM, Decimal



@Engines.register_decorator()
class Engine(BaseOnChain):

    _description = "Sovryn onchain"
    _coinpair = RIF_BTC
    _pool_sc_addr = '0x65528e06371635a338ca804cd65958a11cb11009'
    _wrbtc_tk_addr = '0x542fda317318ebf1d3deaf76e0b632741a7e677d'
    _rif_tk_addr = '0x2acc95758f8b5f583470ba265eb685a8f45fc9d5'

    def _get_value_from_evm(self, evm: EVM):

        rif_reserve_call_id = evm.multicall.add_call(
            self._rif_tk_addr,
            evm.BALANCE_OF,
            self._pool_sc_addr)
        
        btc_reserve_call_id = evm.multicall.add_call(
            self._wrbtc_tk_addr,
            evm.BALANCE_OF,
            self._pool_sc_addr)
        
        evm.multicall.run()

        rif_reserve = evm.multicall.get_call(rif_reserve_call_id)
        btc_reserve = evm.multicall.get_call(btc_reserve_call_id)
        
        value = Decimal(btc_reserve/rif_reserve)
        
        return value, None # (value, str_error)