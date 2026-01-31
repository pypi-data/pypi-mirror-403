from decimal import Decimal
from fnmatch import fnmatch as match
from tabulate import tabulate
from .types import normalize_obj, Serializable
from flask import Flask, request, redirect, jsonify, make_response, current_app
from flask_restx import Api, Resource, reqparse, abort
from flask_cors import CORS
from flask_caching import Cache
from . import get_price, version
from . import ALL as AllCoinPairs
from .cli import command, option
from .redis_conn import use_redis
from .cli_check import show_computed_pairs_fromula, summary, coinpairs_report
from .my_envs import envs



title='MoC prices source API Rest webservice'
description="""

<br>
### Description

This is the API Rest webservice that comes integrated in
the python **moc_prices_source** package.

<br>
### Purpose

Simplify integrations with other environments than **Python**.

<br>
### Refrences

* [Source code in Github](https://github.com/money-on-chain/moc_prices_source)
* [Package from Python package index (PyPI)](https://pypi.org/project/moneyonchain-prices-source)

<br>
<br>

## Endpoints
"""


all_coinpairs = list([str(x) for x in AllCoinPairs])
all_coinpairs.sort()
max_coinpair_limit = envs(
    'MAX_COINPAIR_LIMIT', 12, envs.types.positive_integer)


cache = Cache()
cors = CORS()
api = Api(
    prefix='/api',
    doc='/api/doc',
    version=f"v{version}",
    title=title,
    description=description,
)

def create_app():
    
    app = Flask(__name__)
    
    app.config["CACHE_TYPE"] = "SimpleCache"
    cache.init_app(app)
   
    api.init_app(app)

    app.config["CORS_RESOURCES"] = {r'/*': {"origins": "*"}}
    cors.init_app(app)
    
    @app.before_first_request
    def before_first_request():
        app.logger.setLevel(1)
        app.logger.info(f"{title} (v{version})")
        app.logger.info(f"{len(all_coinpairs)} available coinpairs")
        app.logger.info(f"CONFIG: {use_redis=}")
        app.logger.info(f"CONFIG: {max_coinpair_limit=}")

    return app

app = create_app()



def get_coin_pairs(
        wildcard: str = "*",
        coinpairs_base: list = None
        ) -> list:
    """
    Get all coin pairs that match the wildcard.
    """
    if coinpairs_base is None:
        coinpairs_base =  AllCoinPairs
    wildcards_base = str(wildcard).lower().replace(" ", ",").split(",")
    wildcards = list(set([w for w in wildcards_base if w]))
    coinpairs = []
    for w in wildcards:
        f = filter(lambda i: match(str(i).lower(), w), coinpairs_base)
        f = list(set(list(f)))
        coinpairs.extend(f)
    coinpairs = list(set(coinpairs))
    coinpairs.sort()
    return coinpairs



class CacheKeyMaker():

    def __init__(self, *args, headers=[],
                 info=lambda x: None, pre="") -> None:
        self._pre = pre
        self._info = info
        self._args = list(map(lambda x: str(x).strip().lower(),
                              list(args)))
        self._headers = list(map(lambda x: str(x).strip().lower(),
                                 list(headers)))

    def __call__(self) -> str:
        
        path = request.path
        
        args = {k.lower(): v for k, v in request.args.to_dict(
            flat=True).items()}
        filtered_args = {k: v for k, v in args.items() if k in self._args}
        sorted_args = sorted(filtered_args.items())

        headers = {k.lower(): v for k, v in request.headers.items()}
        filtered_headers = {k: v for k, v in headers.items(
            ) if k in self._headers}
        sorted_headers = sorted(filtered_headers.items())

        key = f"{self._pre}|{path}|{sorted_args}|{sorted_headers}"
        
        self._info(f"cache key = {repr(key)}")

        return key



class HashMethod():

    def __init__(self, *options, info=lambda x: None, pre="") -> None:
        self._pre = pre
        self.info = info
        self.options = list(map(lambda x: str(x).strip().lower(),
                                list(options)))
        self.out = []

    def __call__(self, x) -> None:
        self.out = []
        for key, value in eval(x):
            key=str(key).strip().lower()
            if key in self.options:
                value=str(value).strip().lower()
                if key=='coinpairs' and value:
                    value = ','.join([str(c).lower() for c in get_coin_pairs(
                        value)])
                self.out.append((key, value))
        return self

    def hexdigest(self):
        hash_ = repr(self.out) if self.out else ""
        if self._pre:
            hash_ = f"{self._pre}{hash_}"
        self.info(f"hash = {repr(hash_)}")
        return hash_



@app.after_request
def add_header(response):
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers["Cache-Control"] = 'public, max-age=0'
    return response



@app.before_request
def before_request_func():
    if request.path.startswith('/api/doc'):
        if request.args.get('url'):
            return redirect('/api/doc')



@app.errorhandler(404)
def page_not_found(e):
    if request.path.startswith('/api/'):
        return jsonify(
            code=e.code,
            name=e.name,
            description=e.description
        ), 404
    return redirect('/api/doc')



@app.route('/')
def index():
    return redirect('/api/doc')



coinpairs_ns = api.namespace('coinpairs',
                             description='Coinpairs related operations')



@coinpairs_ns.route('/')
class CoinPairsList(Resource):

    @api.doc(produces=['application/json', 'text/plain'])
    def get(self):
        """Shows a list of all supported coinpairs"""

        accept = request.headers.get('Accept', 'text/plain')
        pairs = AllCoinPairs[:]
        pairs.sort()
        
        if 'text/plain' in accept:
            text = tabulate(
                list([ (str(x),
                        x.name_base,
                        str(x.from_) if x.from_ else '',
                        str(x.to_) if x.to_ else '',
                        x.variant if x.variant else '',
                        x.description or x.short_description
                        ) for x in pairs]),
                headers=['Name', 'Base', 'From', 'To', 'Variant',
                         'Description'],
                tablefmt="simple",
                stralign="left",
                numalign="right"
            )
            response = make_response(text, 200)
            response.mimetype = "text/plain"
            return response
        else:
            return list([{'name': str(x),
                          'base': x.name_base,
                          'from': str(x.from_) if x.from_ else None,
                          'to': str(x.to_) if x.to_ else None,
                          'variant': x.variant,
                          'description': x.description or x.short_description}
                          for x in pairs])



@coinpairs_ns.route('/computed_coinpair_formulas')
class ComputedCoinpairFormulas(Resource):

    @api.doc(produces=['text/plain'])
    def get(self):
        """
        Displays the formulas used for the computed coinpair
        
        In plain text
        """
        
        text = show_computed_pairs_fromula()
        response = make_response(text, 200)
        response.mimetype = "text/plain"
        return response



coinpair_value_get = reqparse.RequestParser()
coinpair_value_get.add_argument(
    'coinpair',
    choices = all_coinpairs,
    type = str,
    help = 'Coinpair symbols')

bad_coinpair_choice = (400, 'Bad coinpair choice')
coinpair_value_not_found = (404, 'Coinpair value not found')

@coinpairs_ns.route('/get_value')
@coinpairs_ns.response(200, 'Success!')
@coinpairs_ns.response(*bad_coinpair_choice)
@coinpairs_ns.response(*coinpair_value_not_found)
class CoinPairValue(Resource):

    @coinpairs_ns.expect(coinpair_value_get)
    @cache.cached(
        timeout=5,
        query_string=True,
        hash_method=HashMethod(
            'coinpair',
            pre="get_coinpair_value",
        )
    )
    def get(self):
        """Get the price of a specific coinpair"""

        args = coinpair_value_get.parse_args()
        coinpair = args['coinpair']

        if coinpair not in all_coinpairs:
            abort(*bad_coinpair_choice)

        current_app.logger.info(
            f"Asking for the value of {coinpair}")

        detail = {}
        value = get_price(
            coinpairs=coinpair,
            detail=detail,
            serializable=True,
            ignore_zero_weighing=True)

        value = normalize_obj(value)

        sources_count = {}
        sources_count_ok = {}
        for p in detail.get('prices', []):
            sub_coinpair = p.get('coinpair', 'unknown')
            sources_count[sub_coinpair] = sources_count.get(
                sub_coinpair, 0) + 1
            if p.get('ok'):
                sources_count_ok[sub_coinpair] = sources_count_ok.get(
                    sub_coinpair, 0) + 1
            else:
                source = p.get('description', 'unknown')
                error = p.get('error', 'unknown')
                if coinpair==sub_coinpair:
                    current_app.logger.warning(f"{coinpair} --> {source} {error}")
                else:
                    current_app.logger.warning(
                        f"{sub_coinpair} for {coinpair} --> {source} {error}")

        for sub_coinpair, p in detail.get('values', {}).items():
            error = p.get('error')
            if error:
                if coinpair==sub_coinpair:
                    current_app.logger.warning(f"{coinpair} --> {error}")
                else:
                    current_app.logger.warning(
                        f"{sub_coinpair} for {coinpair} --> {error}")

        if sources_count:
            sources_count_str = ', '.join(
                [ f"{k}: {sources_count_ok[k]} of {v}"
                 for (k, v) in sources_count.items()])
            if len(sources_count)>1:
                current_app.logger.info(
                    f"Sources count for {coinpair}: {sources_count_str}")
            else:
                current_app.logger.info(f"Sources count for {sources_count_str}")

        if value is None:
            current_app.logger.error(f"Not value for {coinpair}")
            abort(*coinpair_value_not_found)
        else:
            current_app.logger.info(f"Value for {coinpair}: {value}")

        out = {}
        out['required_coinpair'] = coinpair 
        out['value'] = value
        out['detail'] = detail

        return out



@coinpairs_ns.route('/get_value_simple')
@coinpairs_ns.response(200, 'Success!')
@coinpairs_ns.response(*bad_coinpair_choice)
@coinpairs_ns.response(*coinpair_value_not_found)
class CoinPairValueSimple(Resource):

    @coinpairs_ns.expect(coinpair_value_get)
    @cache.cached(
        timeout=5,
        query_string=True,
        hash_method=HashMethod(
            'coinpair',
            pre="get_coinpair_value_simple",
        )
    )
    def get(self):
        """Get the price of a specific coinpair (simple, no details)"""
        return CoinPairValue.get(self)['value']



def get_set_of_prices(*args,
                      detail: dict = {},
                      plain_text: bool = False,
                      plain_text_summary: bool = False,
                      md: bool = False) -> dict:
        
        if not args:
            raise ValueError("No arguments provided")
        
        if len(args)==1:
            if isinstance(args[0], (list, tuple)):
                args = list(args[0])
            else:
                args = [args[0]]
        args = [str(x).strip() for x in args if str(x).strip()]

        if not args:
            raise ValueError("No arguments provided")
        
        wildcard = ','.join(args)
        
        coinpairs = get_coin_pairs(wildcard)

        if not coinpairs:
            raise ValueError("No coinpairs provided")

        if plain_text:
            if plain_text_summary:
                out = summary(
                    coinpairs = coinpairs,
                    md = md)
            else:
                out = coinpairs_report(
                    coinpairs = coinpairs,
                    data = detail)
        else:
            values = get_price(
                coinpairs = coinpairs,
                detail = detail,
                serializable = True,
                ignore_zero_weighing = True)

            if values is None:
                values = {}

            if isinstance(values, (Serializable, Decimal, float, int, bool)):
                values = {coinpairs[0]: values}

            for cp in coinpairs:
                if cp not in values:
                    values[cp] = None

            out = {
                'values': normalize_obj(values),
                'detail': detail
            }
        return out

coinpairs_values_get = reqparse.RequestParser()
coinpairs_values_get.add_argument(
    'coinpairs',
    default="*",
    required=False,    
    type = lambda s: get_coin_pairs(wildcard=s),
    help = 'Set of coinpairs symbols')
bad_coinpairs_set = (400, 'Bad set of coinpairs symbols')
max_coinpairs_reached = (403, 
    f'Forbidden, max number of pairs reached ({max_coinpair_limit})')
coinpairs_value_not_found = (404, 'Non coinpairs value found')

@coinpairs_ns.route('/get_values')
@coinpairs_ns.response(200, 'Success!')
@coinpairs_ns.response(*bad_coinpairs_set)
@coinpairs_ns.response(*max_coinpairs_reached)
@coinpairs_ns.response(*coinpairs_value_not_found)
class CoinPairsValue(Resource):

    @api.doc(produces=['application/json', 'text/plain'])
    @coinpairs_ns.expect(coinpairs_values_get)
    @cache.cached(
        timeout=10,
        key_prefix=CacheKeyMaker(
            'coinpairs',
            headers=['Accept'],
            pre="get_coinpairs_value"))
    def get(self):
        """
        Get the price of a specific set of coinpairs
        
        The __coinpairs__ parameter is required.
        It represents the pairs you want to get the price for.
        
        It supports:

        * A single parameter like __BTC/USD__
        * Multiple parameters in a list, e.g.: __BTC/USD,USD/ARS__
        * Accepts wildcards, e.g., __*/ARS__
        * Or combinations, e.g.: __BTC/USD,*/ARS__

        """

        accept = request.headers.get('Accept', 'text/plain')
        plain_text = 'text/plain' in accept

        args = coinpairs_values_get.parse_args()
        coinpairs = args['coinpairs']

        if not coinpairs:
            abort(*bad_coinpairs_set)

        if len(coinpairs)>max_coinpair_limit:
            abort(*max_coinpairs_reached)

        if len(coinpairs)==1:
            current_app.logger.info(f"Asking for the value of {coinpairs[0]}")
        else:
            current_app.logger.info(f"Asking for the value of {len(coinpairs)} coinpairs")

        detail = {}
       
        out = get_set_of_prices(coinpairs,
                                detail = detail,
                                plain_text = plain_text)

        self._extra_log(coinpairs, detail)

        if not out:
            abort(*coinpairs_value_not_found)       
        
        for coinpair, value in out['values'].items():
            if value is None:
                current_app.logger.error(f"No value for {coinpair}")
            else:
                current_app.logger.info(f"Value for {coinpair}: {value}")

        if plain_text:
            response = make_response(out, 200)
            response.mimetype = "text/plain"
            return response
        else:
            return out

    @staticmethod
    def _extra_log(coinpairs, detail):
        warn, info  = current_app.logger.warning, current_app.logger.info
        values = detail.get('values', {})
        prices = detail.get('prices', {})
        for coinpair in map(str, coinpairs):
            sub_coinpairs = values.get(coinpair, {}).get(
                "requirements", [coinpair])
            sources_count = {}
            sources_count_ok = {}
            for p in prices:
                sub_coinpair = p.get('coinpair', 'unknown')
                if sub_coinpair in sub_coinpairs:
                    sources_count[sub_coinpair] = sources_count.get(
                        sub_coinpair, 0) + 1
                    if p.get('ok'):
                        sources_count_ok[sub_coinpair] = sources_count_ok.get(
                            sub_coinpair, 0) + 1
                    else:
                        source = p.get('description', 'unknown')
                        error = p.get('error', 'unknown')
                        str_value = f"{source} {error}"
                        if coinpair==sub_coinpair:
                            str_title = coinpair
                        else:
                            str_title = f"{sub_coinpair} for {coinpair}"
                        warn(f"{str_title} --> {str_value}")
            if len(sub_coinpairs)>1:
                pass
            if sources_count:
                sources_count_str = ', '.join([
                    f"{k}: {sources_count_ok.get(k, 'N/A')} of {v}"
                    for (k, v) in sources_count.items()])
                if len(sub_coinpairs)>1:
                    str_title = f"Sources count for {coinpair} are"
                else:
                    str_title = "Sources count for"
                info(f"{str_title} {sources_count_str}")



@coinpairs_ns.route('/summary')
@coinpairs_ns.response(200, 'Success!')
@coinpairs_ns.response(*bad_coinpairs_set)
class Summary(Resource):

    @api.doc(produces=['text/markdown', 'text/plain'])
    @coinpairs_ns.expect(coinpairs_values_get)
    @cache.cached(
        timeout=10,
        key_prefix=CacheKeyMaker(
            'coinpairs',
            headers=['Accept'],
            pre="get_summary"))
    def get(self):
        """
        Show how the data is obtained

        Gets a summary of subset of coinpairs or all coinpairs ("*").
        Showing information on how the data is obtained.
        
        It will be displayed in plain text or Markdown.

        The __coinpairs__ parameter is required.
        It represents the pairs you want to get the price for.
        
        It supports:

        * A single parameter like __BTC/USD__
        * Multiple parameters in a list, e.g.: __BTC/USD,USD/ARS__
        * Accepts wildcards, e.g., __*/ARS__
        * Or combinations, e.g.: __BTC/USD,*/ARS__

        """

        accept = request.headers.get('Accept', 'text/plain')
        md = not('text/plain' in accept)

        args = coinpairs_values_get.parse_args()
        coinpairs = args['coinpairs']

        if not coinpairs:
            abort(*bad_coinpairs_set)
      
        out = get_set_of_prices(coinpairs,
                                detail = {},
                                plain_text = True,
                                plain_text_summary = True,
                                md = md)
        
        response = make_response(out, 200)
        response.mimetype = "text/plain"
        return response



@api.route('/info')
class Info(Resource):

    def get(self):
        """Shows API info related"""
        return {
            'name:': title,
            'version' : version,
            'use_redis': use_redis,
            'max_coinpair_limit': max_coinpair_limit
        }



def main(host='0.0.0.0', port=7989, debug=False):
    app.run(debug=debug, host=host, port=port)


@command()
@option('-a', '--addr', 'host', type=str,
        default='0.0.0.0', help='Server host addr.')
@option('-p', '--port', 'port', type=int,
        default=7989, help='Server port.')
@option('-e', '--show-envs', 'show_envs', is_flag=True,
        help='Show used ENV variables used and exit.')
def server_cli(host, port, show_envs=False):
    """MoC prices source API Rest webservice"""
    if show_envs:
        print(envs)
        return
    main(host=host, port=port)



if __name__ == '__main__':
    main(debug=True)
