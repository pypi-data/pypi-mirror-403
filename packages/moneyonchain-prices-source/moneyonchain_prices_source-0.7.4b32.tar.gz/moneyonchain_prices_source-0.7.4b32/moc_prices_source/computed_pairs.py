from .plugins import CoinPairs
from .cli import Output, tabulate



ComputedCoinPairs = dict(
    [ (name, obj) for name, obj in CoinPairs.items() if obj.is_computed ])


computed_pairs = {}
for c in ComputedCoinPairs.values():
    computed_pairs[c] = {
        'requirements': c.requirements,
        'formula': c.formula,
        'formula_desc': c.formula_desc
    }


for name, coinpair in ComputedCoinPairs.items():
    locals()[name] = coinpair
del name, coinpair


def show_computed_pairs_fromula(use_print = False):
    if callable(use_print):
        out = use_print

    else:
        out = Output(print = print if bool(use_print) else None)
    out()
    out("Computed pairs formula")
    out("-------- ----- -------")
    out("")
    table = [[str(pair), '=', data['formula_desc']] for pair,
             data in computed_pairs.items()]
    table.sort()
    out(tabulate(table, tablefmt='plain'))
    out("")
    if isinstance(out, Output):
        return str(out)