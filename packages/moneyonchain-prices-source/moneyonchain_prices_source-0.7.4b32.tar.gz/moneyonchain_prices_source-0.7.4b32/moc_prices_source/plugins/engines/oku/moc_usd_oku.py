from ...pairs.onchain import MOC_USD_OKU
from ...base import BaseOnChain, Engines, get_addr_env, EVM, Decimal



@Engines.register_decorator()
class Engine(BaseOnChain):

    _description = "Oku onchain"
    _coinpair = MOC_USD_OKU
    _addr = get_addr_env('MOC_BTC_ORACLE_ADDR',
                         '0x11683439c9509C135ee4F7bB6e23835e1d86ECBA')

    def _get_value_from_evm(self, evm: EVM):
        value, str_error = None, None
        value_b, ok = evm.call(self._addr, 'peek()(bytes32,bool)')
        if ok:
            value = Decimal(int(value_b.hex(), 16))/Decimal(10**18)
        else:
            str_error = 'invalid or expired price'
        return value, str_error