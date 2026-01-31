import datetime
from os.path import dirname, abspath
from decimal import Decimal
from .coins import Coins
from .pairs import CoinPairs, get_coin_pairs
from .engines import get_coinpair_list, get_engines_names, get_prices, \
    session_storage
from .computed_pairs import computed_pairs
from .weighing import weighing, weighted_median, median, mean
from .types import FancyDecimal, normalize_obj, Serializable
from .app_info import version



base_dir = dirname(abspath(__file__))


__version__ = version


ALL = [c for c in CoinPairs.values()]
for name, coinpair in CoinPairs.items():
    locals()[name] = coinpair
del name, coinpair
for name, coin in Coins.items():
    locals()[name] = coin
del name, coin


def get_price(
    coinpairs = None,
    engines_names = None,
    detail = {},
    weighing = weighing,
    serializable = False,
    ignore_zero_weighing = True): 

    start_time = datetime.datetime.now()

    requested = coinpairs

    if coinpairs:

        if not isinstance(coinpairs, list):
            coinpairs = [coinpairs]

        requested = coinpairs

        new_coinpairs = []
        for c in coinpairs:
            if c in computed_pairs:
                for r in computed_pairs[c]['requirements']:
                    new_coinpairs.append(r)
            elif c in ALL:
                new_coinpairs.append(c)
        coinpairs = list(set(new_coinpairs))

    if 'as_dict' in dir(weighing):
        weighing = weighing.as_dict
    else:
        for key, value in weighing.items():
            weighing[key] = Decimal(str(value))
    
    if ignore_zero_weighing:
        for key in list(weighing.keys()):
            if not weighing[key]:
                del weighing[key]

    if engines_names is None:
        engines_names = list(weighing.keys())

    prices = get_prices(
        coinpairs = coinpairs,
        engines_names = engines_names)

    for value in prices:
        value['weighing'] = weighing.get(value['name'], Decimal('0.0'))

    detail['prices'] = prices

    coinpair_prices = {}
    for value in prices:
        value['percentual_weighing'] = None
        if value['ok']:
            if not value['coinpair'] in coinpair_prices:
                coinpair_prices[value['coinpair']] = {
                    'data': [],
                    'sum_weighing': Decimal('0.0')}
            coinpair_prices[value['coinpair']]['data'].append(value)
            coinpair_prices[value['coinpair']
                            ]['sum_weighing'] += value['weighing']

    for d in coinpair_prices.values():
        sum_weighing = d['sum_weighing']
        for v in d['data']:
            weighing = v['weighing']
            if not weighing:
                percentual_weighing = Decimal('0.0')
            elif not sum_weighing:
                percentual_weighing = Decimal('0.0')
            else:
                percentual_weighing = weighing / sum_weighing
            v['percentual_weighing'] = percentual_weighing

    for k, d in coinpair_prices.items():
        if not 'weighings' in d:
            d['weighings'] = []
        if not 'prices' in d:
            d['prices'] = []
        for v in d['data']:
            d['weighings'].append(v['percentual_weighing'])
            d['prices'].append(v['price'])
        try:
            d['time'] = max(filter(bool, [f.get('time') for f in d['data']]))
        except:
            d['time'] = None
        del d['data']
        del d['sum_weighing']

        ok_sources_count = len(list(filter(bool, d['weighings'])))
        min_ok_sources_count = k.min_ok_sources_count

        d['median_price'] = median(d['prices'])
        d['mean_price'] = mean(d['prices'])
        if any(d['weighings']):
            d['weighted_median_price'] = weighted_median(
                d['prices'], d['weighings'])
        else:
            d['weighted_median_price'] = None

        d['ok_sources_count'] = ok_sources_count
        d['min_ok_sources_count'] = min_ok_sources_count
        d['ok'] = True
        d['error'] = ''
        d['ok_value'] = d['weighted_median_price']

        if ok_sources_count < min_ok_sources_count:
            d['ok'] = False
            d['error'] = ("Not enough price sources "
                          f"({ok_sources_count} < {min_ok_sources_count})")
            d['ok_value'] = None

    if requested:
        requested_computed_pairs = [
            r for r in requested if ((r in computed_pairs) and
                                     (not r in coinpair_prices)) ]
        for r in requested_computed_pairs:
            requirements = computed_pairs[r]['requirements']
            if set(requirements).issubset(set(coinpair_prices.keys())):
                coinpair_prices[r] = {}
                ok = all([ coinpair_prices[q]['ok'] for q in requirements ])
                coinpair_prices[r]['ok'] = ok
                coinpair_prices[r]['requirements'] = requirements
                formula = computed_pairs[r]['formula']               
                args = [coinpair_prices[q]['ok_value'] for q in requirements]
                coinpair_prices[r]['error'] = ''
                coinpair_prices[r]['start_time'] = datetime.datetime.now()
                if not ok:
                    str_pairs = ', '.join([str(q) for q in requirements 
                                           if not(coinpair_prices[q]['ok'])])
                    coinpair_prices[r]['error'] = ("It cannot be calculated"
                        f", is missing values: {str_pairs}.")
                    coinpair_prices[r]['ok_value'] = None
                    coinpair_prices[r]['ok'] = False
                else:
                    try:
                        coinpair_prices[r]['ok_value'] = formula(*args)
                    except Exception as e:
                        coinpair_prices[r]['error'] = str(e)
                        coinpair_prices[r]['ok_value'] = None
                        coinpair_prices[r]['ok'] = False
                coinpair_prices[r]['weighted_median_price'] = \
                    coinpair_prices[r]['ok_value']
                coinpair_prices[r]['time'] = datetime.datetime.now() - \
                    coinpair_prices[r]['start_time']
        
        while True:
            callable_pairs = [r for r in requested_computed_pairs
                              if (coinpair_prices.get(r, {}).get('ok') and
                                  callable(coinpair_prices.get(r, {}).get('ok_value')))]
            if not callable_pairs:
                break
            for r in callable_pairs:
                try:
                    coinpair_prices[r]['ok_value'] = \
                        coinpair_prices[r]['ok_value']()
                except Exception as e:
                    coinpair_prices[r]['error'] = str(e)
                    coinpair_prices[r]['ok_value'] = None
                    coinpair_prices[r]['ok'] = False
                coinpair_prices[r]['weighted_median_price'] = \
                    coinpair_prices[r]['ok_value'] 
                coinpair_prices[r]['time'] = datetime.datetime.now() - coinpair_prices[r]['start_time']
        
        for r in requested_computed_pairs:
            if 'start_time' in coinpair_prices.get(r, {}):
                del coinpair_prices[r]['start_time']


    detail['values'] = coinpair_prices

    out = {}

    for key, value in coinpair_prices.items():
        if requested:
            if key in requested:
                if value['ok']:
                    out[key] = value['ok_value']
        else:
            if value['ok']:
                out[key] = value['ok_value']

    for key in out.keys():
        if type(out[key]) is Decimal:
            out[key] = FancyDecimal(out[key])

    if requested and len(requested)==1:
        if requested[0] in out:
            out = out[requested[0]]
        else:
            out = None

    if not(requested) and  len(out)==1:
        out = list(out.values())[0]

    detail['time'] = datetime.datetime.now() - start_time

    if serializable:
        for k, v in detail.items():
            detail[k] = normalize_obj(v)

    if not out and not(isinstance(out, Serializable)):
        return None

    return out
