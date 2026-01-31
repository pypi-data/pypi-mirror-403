from fnmatch import fnmatch as match
from .plugins import CoinPairs
from .plugins.base import CoinPair, CoinPairType



for name, coinpair in CoinPairs.items():
    locals()[name] = coinpair
del name, coinpair


def get_coin_pair(value):
    value = str(value).strip().lower()
    return dict([ (str(c).strip().lower(), c
                   ) for c in CoinPairs.values() ])[value]


def get_coin_pairs(
        wildcard: str = "*",
        coinpairs_base: list = None
        ) -> list:
    """
    Get all coin pairs that match the wildcard.
    """
    if coinpairs_base is None:
        coinpairs_base = CoinPairs.values()
    wildcards_base = str(wildcard).lower().replace(" ", ",").split(",")
    wildcards = list(set([w for w in wildcards_base if w]))
    coinpairs = []
    for w in wildcards:
        f = filter(lambda i: match(str(i).lower(), w), coinpairs_base)
        f = list(set(list(f)))
        coinpairs.extend(f)
    coinpairs = list(set(coinpairs))
    return coinpairs
