from ...pairs.onchain import BTC_USD_OCH
from ...base import BaseOnChain, Engines, get_addr_env, EVM, Decimal
from ...chains import chain



env = chain.rsk_mainnet.env.btc_usd_oracle_addr

@Engines.register_decorator()
class Engine(BaseOnChain):

    _description = "MOC onchain"
    _coinpair = BTC_USD_OCH
    _addr = get_addr_env(env.name, env.default)

    def _get_value_from_evm(self, evm: EVM):
        value, str_error = None, None
        value_b, ok = evm.call(self._addr, 'peek()(bytes32,bool)')
        if ok:
            value = Decimal(int(value_b.hex(), 16))/Decimal(10**18)
        else:
            str_error = 'invalid or expired price'
        return value, str_error
