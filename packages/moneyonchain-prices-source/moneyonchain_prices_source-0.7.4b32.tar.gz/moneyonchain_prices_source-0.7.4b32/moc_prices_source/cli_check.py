import json
from sys import stderr
from . import version
from . import get_price, ALL, get_coin_pairs
from .cli import Output, command, option, tabulate, trim, cli
from .my_envs import envs
from .weighing import weighing
from .engines import all_engines
from .computed_pairs import show_computed_pairs_fromula, computed_pairs
from .types import FancyDecimal, FancyTimedelta, Decimal, timedelta
from .my_logging import set_level, OFF, INFO, DEBUG, VERBOSE
from .pairs import CoinPairType
from textwrap import wrap



def summary(coinpairs,
            md = False,
            use_print = False):
    
    if callable(use_print):
        out = use_print
    else:
        out = Output(print = print if bool(use_print) else None)

    summary_data = {}

    for name, weigh in weighing.as_dict.items():
        if name in all_engines:
            engine = all_engines[name]
            coinpair = engine.coinpair
            description = engine.description
            uri = engine.uri

            if not coinpair in summary_data:
                summary_data[coinpair] = {'type': coinpair.type,
                                          'sources': []}
            
            summary_data[coinpair]['sources'].append({
                'weigh': weigh, 'name': description, 'uri': uri
            })

    for computed_coinpair, computed_data in computed_pairs.items():
        if not computed_coinpair in summary_data:
            requirements = computed_data['requirements']
            if all([(c in summary_data) for c in requirements]):
                if not computed_coinpair in summary_data:
                    summary_data[computed_coinpair] = {
                        'type': computed_coinpair.type,
                        'requirements': requirements,
                        'formula': computed_data['formula'],
                        'formula_desc': computed_data['formula_desc']
                    }


    coinpairs_and_requirements = coinpairs[:]
    for coinpair in coinpairs:
        c_data = summary_data.get(coinpair, None) 
        if c_data and c_data['type'] in [CoinPairType.COMPUTED,
                                         CoinPairType.INVERTED]:
            for r in c_data['requirements']:
                if not r in coinpairs_and_requirements:
                    coinpairs_and_requirements.append(r)


    for key in list(summary_data.keys()):
        if not key in coinpairs_and_requirements:
            del summary_data[key]

    def show_title(title, level=1):
        if md:
            prev = {1:"## ", 2:"### "}[level]
            out(prev + ' '.join(title.split()))
        else:
            prev = {1:"", 2:"  "}[level]
            sep = {1:"=", 2:"-"}[level]
            out(prev + ' '.join(title.split()))
            out(prev + ' '.join(map(lambda x: sep*len(x), title.split())))

    def show_p(p):
        if md:
            out(p)
        else:
            out(f"    {p}")

    def show_table(table, headers=[], tablefmt='psql'):
        if md:
            if tablefmt=='psql':
                tablefmt='github'
        s = tabulate(table, headers=headers, tablefmt=tablefmt,
                     floatfmt=".2f")
        if md:
            if tablefmt=='plain':
                out('```')
            out(s)
            if tablefmt=='plain':
                out('```')
        else:
            if tablefmt=='plain':
                s = tabulate([[s]], tablefmt='psql')        
            for l in s.split('\n'):
                out(f"    {l}")

    title = "Symbols"
    coins = []
    for pair in summary_data.keys():
        for c in [pair.from_, pair.to_]:
            if c is not None and not c in coins:
                coins.append(c)
    coins.sort()
    table = [[c.symbol, c.name, c.small_symbol] for c in coins]
    table.sort()
    headers=['Symbol', 'Name', 'Char']
    out()
    show_title(title)
    out()
    show_table(table, headers)
    out()

    title = "Coinpairs"
    table = [[str(pair), pair.name_base, pair.variant,
             str(data['type']).capitalize()
             ] for pair, data in summary_data.items()]
    table.sort()
    headers=['Name', 'Coinpair', 'Variant', 'Method']
    out()
    show_title(title)
    out()
    show_table(table, headers)
    out()
    table = [[str(k).capitalize(), v] for k, v in CoinPairType.as_dict.items()
             if k in [data['type']for data in summary_data.values()]]
    table.sort()      
    headers=['Method', 'Description']
    show_table(table, headers)
    out()
    table = [[str(pair), pair.description] for pair, data in summary_data.items()]
    table.sort()
    headers=['Name', 'Comment/Description']
    show_table(table, headers)
    out()    

    title="Formulas used in the computed coinpairs"
    table=[[str(pair), '=', data['formula_desc']] for pair, data in
           summary_data.items() if data['type'] in [CoinPairType.COMPUTED,
                                                    CoinPairType.INVERTED]]
    table.sort()
    out()
    show_title(title)
    out()
    show_table(table, tablefmt='plain')
    out()

    title="Weights used for each obtained coinpairs from multiple sources"
    out()
    show_title(title)
    out()
    show_p("""If a price source is not available, this source is discarded
and the rest of the sources are used but with their weights recalculated
proportionally.""")
    show_p("""For example, you have 3 sources with 3 weights A:0.2, B:0.5, C:0.3
and if for some reason B would not be available, A:0.4, C:0.6 would
be used.""")
    out()
    show_p("""The weights used are fixed values.""")
    show_p("""These weightings are related to the historical volume handled by each
price source.""")
    show_p("""Every established period of time we review the historical volume of the
sources and if necessary we apply the changes to the parameterization.""")
    out()
    for pair, data in summary_data.items():
        if not(data['type'] in [CoinPairType.COMPUTED,
                                CoinPairType.INVERTED,
                                CoinPairType.DUMMY]):
            title = f"For coinpair {pair.long_name}"
            sources = data['sources']
            table = [[d['name'], float(d['weigh']), d['uri']] for d in
                     sources if float(d['weigh'])>0]
            headers=['Source', 'Weight', 'URI']
            if table:
                out()
                show_title(title, 2)
                out()
                if len(table)>1:
                    show_table(table, headers)
                else:
                    show_p(f"Only {table[0][0]} (URI: {table[0][2]})")
                out()
    if isinstance(out, Output):
        return str(out)


def coinpairs_report(coinpairs,
           show_json = False,
           not_ignore_zero_weighing = False,
           expand_values = False,
           use_print = False,
           data = {}):
    
    get_price(
        coinpairs,
        ignore_zero_weighing = not(not_ignore_zero_weighing),
        detail = data,
        serializable = show_json)

    if show_json:
        return json.dumps(data, indent=4, sort_keys=True)

    if callable(use_print):
        out = use_print
    else:
        out = Output(print = print if bool(use_print) else None)

    time = data['time']
    prices = data['prices']
    values = data['values']

    table=[]
    prices_count = {}
    for p in prices:
        row = []
        row.append(p["coinpair"].name_base)
        row.append(p["coinpair"].variant)
        row.append(p["coinpair"].short_description)
        row.append(p["description"])
        if not p["coinpair"] in prices_count:
            prices_count[p["coinpair"]] = 0
        prices_count[p["coinpair"]] += 1
        if p["ok"]:
            if p['coinpair'].to_ is None:
                row.append(f"{p['price']}")
            else:
                unit = 'p'
                v = p['price'] * (1000**4)
                if v > 1000:
                    for unit in ['p', 'µ', 'm', ' ', 'K', 'M', 'G']:
                        v = v/1000
                        if v<1000:
                            break
                row.append(f"{p['coinpair'].to_.small_symbol} {v:9.5f}{unit}")
        else:
            row.append(trim(p["error"], 20))
        row.append(round(p["weighing"], 2))
        if p["percentual_weighing"]:
            row.append(round(p[
                "percentual_weighing"]*100, 1))
        else:
            row.append('N/A')
        if p["time"]:
            row.append(str(FancyTimedelta(p["time"])))
        else:
            row.append('N/A')
        table.append(row)
    
    if table:
        table.sort(key=str)
        out()
        out(tabulate(table, headers=[
            'Coinpair', 'V.', 'Short description', 'Exchnage', 'Response',
            'Weight', '%', 'Time'
        ]))

    table=[]
    for coinpair, d in values.items():
        row = []
        if coinpair.type == CoinPairType.COMPUTED:
            row.append('ƒ')
        elif coinpair.type == CoinPairType.DIRECT:
            row.append('↓')
        elif coinpair.type == CoinPairType.WEIGHTED:
            row.append('⇓')
        elif coinpair.type == CoinPairType.ONCHAIN:
            row.append('⛓')
        elif coinpair.type == CoinPairType.DUMMY:
            row.append('=')
        elif coinpair.type == CoinPairType.INVERTED:
            row.append('⇄')
        else:
            row.append('·')        
        row.append(coinpair)
        if expand_values:
            row.append(d['median_price'] if 'median_price' in d else None)
            row.append(d['mean_price'] if 'mean_price' in d else None)
        row.append(d['weighted_median_price'])
        if 'prices' in d:
            if 'ok_sources_count' in d:
                row.append(
                    f"{d['ok_sources_count']} of {prices_count[coinpair]}")
            else:
                row.append(len(d['prices']))
        else:
            row.append('N/A')
        row.append('✓' if d['ok'] else '✕')
        row.append(d['time'] if 'time' in d else None)
        table.append(row)
    if table:
        table.sort(key=lambda x: str(x[1]))
        out()
        def format_field(x):
            if type(x) is Decimal:
                x = FancyDecimal(x)
            if type(x) is timedelta:
                x = FancyTimedelta(x)
            return str(x)
        table = [[format_field(f) for f in l] for l in table]
        if expand_values:
            headers=['', 'Coinpair', 'Mediam', 'Mean',
                     'Weighted median', 'Sources', 'Ok', 'Time']
            colalign=['center', 'left', 'right', 'right',
                      'right', 'center', 'center', 'left']
        else:
            headers=['', 'Coinpair', 'Value', 'Sources count', 'Ok', 'Time']
            colalign=['center', 'left', 'right', 'center', 'center', 'left']
        out(tabulate(table, headers=headers, colalign=colalign))

    errors = []
    for p in prices:
        if not p["ok"] and p['weighing']:
            str_error = '\n'.join(wrap(str(p["error"]),width=40,break_long_words=True,break_on_hyphens=False))
            errors.append((f"Source {p['name']}:", str_error))
    for k, v in values.items():
        if 'error' in v and v["error"]:
            str_error = '\n'.join(wrap(str(v["error"]),width=40,break_long_words=True,break_on_hyphens=False))   
            errors.append((f"Coinpair {k}:", str_error))    

    if errors:
        out()
        out("Errors detail")
        out("------ ------")
        for l in tabulate(errors, tablefmt='plain').split('\n'):
            if l[0]!=' ':
                out()
            out(f"  {l}")

    out()
    out('Response time {}'.format(FancyTimedelta(time)))
    out()

    if isinstance(out, Output):
        return str(out)


@command()
@option('-v', '--verbose', 'verbose', count=True,
    help='Verbose mode.')
@option('--version', 'show_version', is_flag=True,
        help='Show version and exit.')
@option('-j', '--json', 'show_json', is_flag=True,
        help='Show data in JSON format and exit.')
@option('-w', '--weighing', 'show_weighing', is_flag=True,
        help='Show the default weighing and exit.')
@option('-c', '--computed', 'show_computed_pairs', is_flag=True,
        help='Show the computed pairs formula and exit.')
@option('-e', '--show-envs', 'show_envs', is_flag=True,
        help='Show used ENV variables used and exit.')
@option('-s', '--summary', 'show_summary', is_flag=True,
        help='Show the summary and exit.')
@option('-m', '--markdown', 'md_summary', is_flag=True,
        help='Set markdown for the summary format.')
@option('-n', '--not-ignore-zero-weighing', 'not_ignore_zero_weighing',
        is_flag=True, help='Not ignore sources with zero weighing.')
@cli.argument('coinpairs_filter', required=False)
def cli_check(
        show_version=False,
        show_json=False,
        show_weighing=False,
        show_computed_pairs=False,
        coinpairs_filter=None,
        show_summary=False,
        md_summary=False,
        not_ignore_zero_weighing=False,
        expand_values=False,
        show_envs=False,
        verbose = 0
    ):
    """\b
Description:
    CLI-type tool that shows the data obtained by
    the `moc_price_source` library.   
    Useful for troubleshooting.
\n\b
COINPAIRS_FILTER:
    Is a display pairs filter that accepts wildcards.
    Example: "btc*"
    Default value: "*" (all available pairs)
"""

    # Logger
    if verbose==0:
        level = OFF
    elif verbose==1:
        level = INFO
    elif verbose==2:
        level = VERBOSE
    elif verbose>2:
        level = DEBUG
    set_level(level)

    if md_summary and not show_summary:
        print(
            "Error: '-m', '--markdown' option only works "
            "with '-s', '--summary'",
            file=stderr)
        return 1

    if show_version:
        print(version)
        return

    if show_weighing:
        if show_json:
            print(weighing.as_json)
        else:
            print()
            print(weighing)
            print()
        return

    if show_computed_pairs:
        show_computed_pairs_fromula(use_print = True)
        return 

    if coinpairs_filter:
        coinpairs = get_coin_pairs(coinpairs_filter)
    else:
        coinpairs = ALL
    if not coinpairs:
        print(
            f"The {repr(coinpairs_filter)} filter did not return "
            "any results.",
            file=stderr)
        return 1
    
    if show_summary:
        summary(coinpairs, md_summary,
                use_print = True)
        return

    if show_envs:
        print(envs)
        return

    coinpairs_report(
        coinpairs,
        show_json = show_json,
        not_ignore_zero_weighing = not_ignore_zero_weighing,
        expand_values = expand_values,
        use_print = True)



if __name__ == '__main__':
    exit(cli_check())
