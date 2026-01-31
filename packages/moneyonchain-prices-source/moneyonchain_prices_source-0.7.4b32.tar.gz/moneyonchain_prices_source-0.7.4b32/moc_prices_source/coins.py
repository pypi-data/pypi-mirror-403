from .plugins import Coins



for name, coin in Coins.items():
    locals()[name] = coin
del name, coin


def get_coin(value):
    value = str(value).strip().lower()
    try:
        return dict([ (str(c.name).strip().lower(), c
                       ) for c in Coins.values()])[value]
    except KeyError:
        return dict([ (str(c).strip().lower(), c
                       ) for c in Coins.values()])[value]
