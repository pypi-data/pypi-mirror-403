from ..base import CoinPairs, CoinPair, CoinPairType 
from ..coins import BTC, DOC, RIF, USD, USDT



# Special pairs

#Rootstock block number
BLOCK_RSK = CoinPair(name="BLOCK", variant="RSK",
                     short_description = "Rootstock block number",
                     type_ = CoinPairType.ONCHAIN)

# DOC/USD
DOC_USD = CoinPair(DOC, USD, short_description="Pegged 1:1 to USD",
                   type_ = CoinPairType.DUMMY)

# RIF/BTC
RIF_BTC_MP1P = CoinPair(RIF, BTC, "mp1%",
                        description = "To move the price 1 percent",
                        short_description = "To move the price 1%",
                        type_ = CoinPairType.DIRECT)

# RIF/USDT
RIF_USDT_MP1P = CoinPair(RIF, USDT, "mp1%",
                        description = "To move the price 1 percent",
                        short_description = "To move the price 1%",
                        type_ = CoinPairType.DIRECT)

CoinPairs.register()
