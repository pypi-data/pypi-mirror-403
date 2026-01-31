from .simple import BTC_ARS, BTC_COP, BTC_USD
from .onchain import BPRO_BTC
from ..chains import EVM, chain
from ..base import CoinPairs, CoinPair, Formula, Decimal
from ...types import PercentageDecimal, Yes, No
from ...evm import Address



### Computed onchain pairs

# BTC_USD_24h
if chain.rsk_mainnet.enabled and \
    chain.rsk_mainnet.btc_usd_oracle_addr!=Address(0):

    class BTC_USD_24h_Formula(Formula):

        evm: EVM = chain.rsk_mainnet.evm
        oracle_addr = chain.rsk_mainnet.btc_usd_oracle_addr
        coinpair = BTC_USD
        requirements = [coinpair]
        hours: int = 24

        __doc__ = (f"({coinpair}@NOW - {coinpair}@{hours}hAGO)"
                f" / {coinpair}@{hours}hAGO")

        def init(self, btc_usd):
            self.block = (self.evm.latest_block_number
                        - int(3600 * self.hours / 25))
            self.call_id = self.evm.multicall.add_call(
                self.oracle_addr, 'peek()(bytes32,bool)')
            self._namespace = f"{self.hours}h ago"

        def step(self, value, btc_usd):
            self.evm.multicall.run_only_first_time(
                block_identifier = self.block,
                namespace = self._namespace)
            value_b, ok = self.evm.multicall.get_call(
                self.call_id, namespace = self._namespace)
            if ok:
                btc_usd_before = (Decimal(int(value_b.hex(), 16))
                                / Decimal(10**18))
            else:
                raise ValueError('invalid or expired price')
            return PercentageDecimal((btc_usd - btc_usd_before)
                                     / btc_usd_before)
        
        def cleanup(self):
            self.evm.multicall.clear_calls()

    BTC_USD_24h = CoinPair(
        name = "BTC/USD(24h)",
        description = "BTC/USD percentage difference over 24 hours",
        requirements = BTC_USD_24h_Formula.requirements,
        formula = BTC_USD_24h_Formula)


class ISLIQ_FLIP_Formula(Formula):
    """
        MultiCollateralGuard.readyToLiquidate([
            [bpro_ars, bpro_cop],
            [usd_ars, usd_cop]
        ])
    """

    evm: EVM = ...
    mcg_addr = ...
    mcg_addr_env = ...

    requirements = [BTC_ARS, BTC_COP, BTC_USD, BPRO_BTC]
    fn_list = ['readyToLiquidate(uint256[][])(bool)',
               'readyToMicroLiquidate(uint256[][])(bool)']

    def init(self, btc_ars, btc_cop, btc_usd, bpro_btc):
                       
        wei = lambda value: int(value * Decimal("1e18"))

        usd_ars = wei(btc_ars / btc_usd)
        usd_cop = wei(btc_cop / btc_usd)
        bpro_ars =  wei(bpro_btc * btc_ars)
        bpro_cop = wei(bpro_btc * btc_cop)
        
        call_args = [
                [bpro_ars, bpro_cop],
                [usd_ars, usd_cop]
            ]
        
        self.call_ids = []
        for fn_spec in self.fn_list:
            self.call_ids.append(
                self.evm.multicall.add_call(self.mcg_addr, fn_spec, call_args)
            )
        
    def step(self, *args):
        self.evm.multicall.run_only_first_time()
        values = list(map(self.evm.multicall.get_call, self.call_ids))

        if all([ans is not None for ans in values]):
            return Yes if any(values) else No
        else:
            env = self.mcg_addr_env
            addr = Address(self.mcg_addr).make_abbreviation(sep='...')
            fn_list = [f"{fn.split('(')[0]}(...)" for v, fn in zip(
                values, self.fn_list) if v is None]
            fn_str = (' and '.join([', '.join(fn_list[:-1]), fn_list[-1]]
                                   ) if len(fn_list)>1 else fn_list[-1])
            msg = (f"Error calling {fn_str} in multiCollateralGuard({addr}). "
                   f"Maybe the address passed by the {env} environment "
                   "variable is incorrect.")
            raise ValueError(msg)

    def cleanup(self):
        self.evm.multicall.clear_calls()


# ISLIQ_FLIP
if chain.rsk_mainnet.enabled and chain.rsk_mainnet.mcg_addr!=Address(0):

    class ISLIQ_FLIP_MAIN_Formula(ISLIQ_FLIP_Formula):
        evm: EVM = chain.rsk_mainnet.evm
        mcg_addr = chain.rsk_mainnet.mcg_addr
        mcg_addr_env = chain.rsk_mainnet.env.mcg_addr.name

    ISLIQ_FLIP = CoinPair(
        name="ISLIQ_FLIP",
        short_description = "If FLip is in liquidation (mainnet)",
        requirements = ISLIQ_FLIP_MAIN_Formula.requirements,
        formula = ISLIQ_FLIP_MAIN_Formula)


# ISLIQ_FLIP_TEST
if chain.rsk_testnet.enabled and chain.rsk_testnet.mcg_addr!=Address(0):

    class ISLIQ_FLIP_TEST_Formula(ISLIQ_FLIP_Formula):
        """
            MultiCollateralGuardTestnet.readyToLiquidate([
                [bpro_ars, bpro_cop],
                [usd_ars, usd_cop]
            ])
        """

        evm: EVM = chain.rsk_testnet.evm
        mcg_addr = chain.rsk_testnet.mcg_addr
        mcg_addr_env = chain.rsk_testnet.env.mcg_addr.name
    
    ISLIQ_FLIP_TEST = CoinPair(
        name="ISLIQ_FLIP",
        variant="test",
        short_description = "If FLip is in liquidation (testnet)",
        requirements = ISLIQ_FLIP_TEST_Formula.requirements,
        formula = ISLIQ_FLIP_TEST_Formula)


CoinPairs.register()
