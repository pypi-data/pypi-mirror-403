from ...pairs.special import BLOCK_RSK
from ...base import BaseOnChain, Engines, EVM



@Engines.register_decorator()
class Engine(BaseOnChain):

    _description = "RSK onchain"
    _coinpair = BLOCK_RSK

    def _get_value_from_evm(self, evm: EVM):
        value = evm.latest_block_number
        return value, None # (value, str_error)
    