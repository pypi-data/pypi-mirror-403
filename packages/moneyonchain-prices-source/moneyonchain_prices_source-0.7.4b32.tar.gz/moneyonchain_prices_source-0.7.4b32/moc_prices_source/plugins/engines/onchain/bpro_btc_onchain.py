from ...pairs.onchain import BPRO_BTC
from ...base import BaseOnChain, Engines, get_addr_env, EVM, Decimal



@Engines.register_decorator()
class Engine(BaseOnChain):

    _description = "MOC onchain"
    _coinpair = BPRO_BTC
    _addr = get_addr_env('MOC_STATE_ADDR',
                         '0xb9C42EFc8ec54490a37cA91c423F7285Fa01e257')

    def _get_value_from_evm(self, evm: EVM):
        value_wei = evm.call(self._addr, 'bproTecPrice()(uint256)')
        value = Decimal(value_wei)/Decimal(10**18)
        return value, None # (value, str_error)