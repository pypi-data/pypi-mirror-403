from .base import Engines, CoinPairs, Coins
from ..cli import command_group, command, argument, BadParameter, print_list



@command_group()
def cli():
    """ Help for moc_prices_source plugins. """


@command(cli)
def coins():
    """ List available coins. """
    print_list(Coins.keys())


@command(cli)
def pairs():
    """ List available coin pairs. """
    print_list(CoinPairs.keys())


@command(cli)
def engines():
    """ List available engines. """
    print_list(Engines.keys())


def validate_engine(ctx, param, value):
    if value not in Engines:
        raise BadParameter(f"'{value}' not a valid engine.")
    return value


@command(cli)
@argument("engine", callback=validate_engine)
def test(engine):
    """ Test a single engine. """
    engine = Engines[engine]()
    engine()
    print(f"URI = {repr(engine.uri)}")
    print()
    print(engine)
    print()
    if engine.error:
        print()
        print(engine.error)
        print()



if __name__ == "__main__":
    cli()
