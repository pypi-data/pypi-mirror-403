import pkgutil, traceback, importlib
from .base import Engines, CoinPairs, Coins



exclude = ['base']

for module_info in pkgutil.walk_packages(
    __path__,
    prefix=f"{__name__}."):
    
    name = module_info.name
    basename = name.split('.')[-1]
    
    if basename.startswith('_') or basename in exclude:
        continue

    try:
        importlib.import_module(name)
    except Exception:
        traceback.print_exc()


__all__ = ["Engines", "CoinPairs", "Coins"]
