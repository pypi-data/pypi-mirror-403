from ...pairs.onchain import MOC_BTC_SOV
from ...base import BaseOnChain, Engines, EVM, Decimal



@Engines.register_decorator()
class Engine(BaseOnChain):

    _description = "Sovryn onchain"
    _coinpair = MOC_BTC_SOV
    _pool_sc_addr = '0xe321442dc4793c17f41fe3fb192a856a4864ceaf'
    _wrbtc_tk_addr = '0x542fda317318ebf1d3deaf76e0b632741a7e677d'
    _moc_tk_addr = '0x9ac7fe28967b30e3a4e6e03286d715b42b453d10'

    def _get_value_from_evm(self, evm: EVM):

        moc_reserve_call_id = evm.multicall.add_call(
            self._moc_tk_addr,
            evm.BALANCE_OF,
            self._pool_sc_addr)
        
        btc_reserve_call_id = evm.multicall.add_call(
            self._wrbtc_tk_addr,
            evm.BALANCE_OF,
            self._pool_sc_addr)
        
        evm.multicall.run()

        moc_reserve = evm.multicall.get_call(moc_reserve_call_id)
        btc_reserve = evm.multicall.get_call(btc_reserve_call_id)
        
        value = Decimal(btc_reserve/moc_reserve)

        return value, None # (value, str_error)