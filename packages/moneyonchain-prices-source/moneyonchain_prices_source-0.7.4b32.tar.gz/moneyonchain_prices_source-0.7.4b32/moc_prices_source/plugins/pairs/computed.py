from ...weighing import weighted_median
from ...weighing import median as Median
from ..base import CoinPairs, CoinPair, Formula
from ..coins import BTC, USD, RIF, MOC, ETH, USDT, BNB, ARS, COP, BPRO
from .simple import BNB_USDT,  BTC_ARS, BTC_COP, BTC_USD, BTC_USDT, \
    ETH_BTC, RIF_USDT, RIF_USDT_MA, USDT_USD, RIF_BTC
from .onchain import BPRO_BTC, MOC_BTC_SOV, MOC_USD_OKU



# Computed pairs

# BNB/USD
BNB_USD = CoinPair(BNB, USD,
    requirements = [BNB_USDT, BTC_USD, BTC_USDT],
    formula = lambda bnb_usdt, btc_usd, btc_usdt\
        : bnb_usdt * btc_usd / btc_usdt)

# BPRO/ARS
BPRO_ARS = CoinPair(BPRO, ARS,
    requirements = [BPRO_BTC, BTC_ARS],
    formula = lambda bpro_btc, btc_ars: bpro_btc * btc_ars)

# BPRO/COP
BPRO_COP = CoinPair(BPRO, COP,
    requirements = [BPRO_BTC, BTC_COP],
    formula = lambda bpro_btc, btc_cop: bpro_btc * btc_cop)

# BPRO/USD
BPRO_USD = CoinPair(BPRO, USD,
    description = "Offchain",
    requirements = [BPRO_BTC, BTC_USD],
    formula = lambda bpro_btc, btc_usd: bpro_btc * btc_usd)

# ETH/USD
ETH_USD_B = CoinPair(ETH, USD, "B",
    description = "Passing through Bitcoin",
    requirements = [ETH_BTC, BTC_USD],
    formula = lambda eth_btc, btc_usd: eth_btc * btc_usd)

# MOC/BPRO
MOC_BPRO = CoinPair(MOC, BPRO,
    requirements = [MOC_BTC_SOV, BTC_USD, MOC_USD_OKU, BPRO_BTC],
    formula = lambda moc_btc_sov, btc_usd, moc_usd_oku, bpro_btc\
        : Median((moc_btc_sov * btc_usd), moc_usd_oku) / btc_usd * bpro_btc)

# MOC/BTC
MOC_BTC = CoinPair(MOC, BTC,
    requirements = [MOC_BTC_SOV, BTC_USD, MOC_USD_OKU],
    formula = lambda moc_btc_sov, btc_usd, moc_usd_oku\
        : Median((moc_btc_sov * btc_usd), moc_usd_oku) / btc_usd)

# MOC/USD
MOC_USD = CoinPair(MOC, USD,
    description = "Default option, weighted median",
    requirements = [MOC_BTC_SOV, BTC_USD, MOC_USD_OKU],
    formula = lambda moc_btc_sov, btc_usd, moc_usd_oku\
        : Median((moc_btc_sov * btc_usd), moc_usd_oku))

MOC_USD_SOV = CoinPair(MOC, USD, description = "Sovryn",
    requirements = [MOC_BTC_SOV, BTC_USD],
    formula = lambda moc_btc_sov, btc_usd: moc_btc_sov * btc_usd)

MOC_USD_WM = CoinPair(MOC, USD, "WM", "Weighted median",
    requirements = [MOC_BTC_SOV, BTC_USD, MOC_USD_OKU],
    formula = lambda moc_btc_sov, btc_usd, moc_usd_oku\
        : Median((moc_btc_sov * btc_usd), moc_usd_oku))

# RIF/USD
RIF_USD = CoinPair(RIF, USD,
    description = "Leave this as legacy",
    requirements = [RIF_BTC, BTC_USD],
    formula = lambda rif_btc, btc_usd: rif_btc * btc_usd)

RIF_USD_B = CoinPair(RIF, USD, "B",
    description = "Passing through Bitcoin",
    requirements = [RIF_BTC, BTC_USD],
    formula = lambda rif_btc, btc_usd: rif_btc * btc_usd)

RIF_USD_T = CoinPair(RIF, USD, "T",
    description = "Passing through Tether",
    requirements = [RIF_USDT, USDT_USD],
    formula = lambda rif_usdt, usdt_usd: rif_usdt * usdt_usd)

RIF_USD_TB = CoinPair(RIF, USD, "TB",
    description = "Passing through Tether & Bitcoin",
    requirements = [RIF_USDT, BTC_USD, BTC_USDT],
    formula = lambda rif_usdt, btc_usd, btc_usdt\
        : rif_usdt * btc_usd / btc_usdt)

RIF_USD_TBMA = CoinPair(RIF, USD, "TBMA",
    description = "Passing through Tether & Bitcoin, "
                  "using [WDAP](fundamentals/wdap.md)",
    requirements = [RIF_USDT_MA, BTC_USD, BTC_USDT],
    formula = lambda rif_usdt_ma, btc_usd, btc_usdt\
        : rif_usdt_ma * btc_usd / btc_usdt)

RIF_USD_TMA = CoinPair(RIF, USD, "TMA",
    description = "Passing through Tether, "
                  "using [WDAP](fundamentals/wdap.md)",
    requirements = [RIF_USDT_MA, USDT_USD],
    formula = lambda rif_usdt_ma, usdt_usd: rif_usdt_ma * usdt_usd)

class RIF_USD_WMTB_Formula(Formula):
    """
    Weighted(
      (rif_usdt × btc_usd / btc_usdt) at 75%,
      (rif_btc × btc_usd) at 25%
    )
    """    
    @staticmethod
    def formula(rif_usdt, btc_usd, btc_usdt, rif_btc):
        return weighted_median(
            [(rif_usdt * btc_usd / btc_usdt), (rif_btc * btc_usd)],
            [0.75, 0.25])

RIF_USD_WMTB = CoinPair(RIF, USD, "WMTB",
    description = "Passing through Tether & Bitcoin using weighted median",
    requirements = [RIF_USDT, BTC_USD, BTC_USDT, RIF_BTC],
    formula = RIF_USD_WMTB_Formula)

# USD/ARS
USD_ARS_CCB = CoinPair(USD, ARS, "CCB",
    description = "Paid in Bitcoin",
    requirements = [BTC_ARS, BTC_USD],
    formula = lambda btc_ars, btc_usd: btc_ars / btc_usd)

# USD/COP
USD_COP_CCB = CoinPair(USD, COP, "CCB",
    description = "Paid in Bitcoin",
    requirements = [BTC_COP, BTC_USD],
    formula = lambda btc_cop, btc_usd: btc_cop / btc_usd)

# USDT/USD
USDT_USD_B = CoinPair(USDT, USD, "B", "Passing through Bitcoin",
    requirements = [BTC_USD, BTC_USDT],
    formula = lambda btc_usd, btc_usdt: btc_usd / btc_usdt)

CoinPairs.register()
