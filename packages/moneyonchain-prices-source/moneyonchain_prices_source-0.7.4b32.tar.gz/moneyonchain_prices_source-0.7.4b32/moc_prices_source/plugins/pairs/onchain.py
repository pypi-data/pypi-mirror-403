from ..base import CoinPairs, CoinPair, CoinPairType
from ..coins import BPRO, BTC, GAS, MOC, USD



# Onchain pairs 

# BPRO/BTC
BPRO_BTC = CoinPair(BPRO, BTC,
                    description = "Obtained from MOC onchain",
                    type_= CoinPairType.ONCHAIN)

# BTC/USD
BTC_USD_OCH = CoinPair(BTC, USD, "och",
                       description = "Obtained from the blockchain",
                       type_= CoinPairType.ONCHAIN)

# GAS/BTC Rootstock gas price from nodes
GAS_BTC = CoinPair(GAS, BTC,
                   description = "Rootstock gas price from nodes",
                   short_description = "Rootstock gas price",
                   type_= CoinPairType.ONCHAIN)

# MOC/BTC
MOC_BTC_SOV = CoinPair(MOC, BTC, "sov",
                       description = "Obtained from Sovryn onchain",
                       type_= CoinPairType.ONCHAIN)

# MOC/USD
MOC_USD_OKU = CoinPair(MOC, USD, "Oku",
                          description = "Obtained from Oku onchain",
                          type_= CoinPairType.ONCHAIN)

CoinPairs.register()
