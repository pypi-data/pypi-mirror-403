from ...pairs.onchain import GAS_BTC
from ...base import BaseOnChain, Engines, EVM, Decimal



@Engines.register_decorator()
class Engine(BaseOnChain):

    _description = "RSK onchain"
    _coinpair = GAS_BTC
    _max = Decimal(2*(10**10)) #20Gwei

    def _get_value_from_evm(self, evm: EVM):
        value = evm.gas_price
        if not value:
            str_error = f"No gas price value given from {self._uri}"
            return None, str_error # (value, str_error)
        elif value >= self._max:
            str_error = f"Gas price value >= {self._max}"
            return None, str_error # (value, str_error)
        else:
            return value, None # (value, str_error)
