# **MoC prices source**

This is the python package used in [**Money on Chain**](https://moneyonchain.com/) projects where it is required to get the coinpair values directly from the sources.
This package includes a CLI tool that allows you to query the coinpair values in the same way that [**Money on Chain**](https://moneyonchain.com/) projects do.



## How to use it in your project

A simple example, do some imports first

```python
user@host:~$ python3 -q
>>> from moc_prices_source import get_price, BTC_USD
>>>
```

Get de `BTC/USD` coin pair

```python
>>> get_price(BTC_USD)
Decimal('89561.50000')
>>> 
```

And that's it!

More [usage examples](docs/examples.md) can be seen [here](docs/examples.md)



## How the included CLI tool looks like

Here you can see how the output of the `moc_prices_source_check` command looks like

```shell
user@host:~$ moc_prices_source_check "BTC/USD*"

Coinpair    V.    Short description    Exchnage     Response        Weight    %  Time
----------  ----  -------------------  -----------  ------------  --------  ---  ------
BTC/USD     och   Bitcoin to Dollar    MOC onchain  $  89.08900K      1     100  1.66s
BTC/USD           Bitcoin to Dollar    Bitfinex     $  89.18400K      0.18   18  214ms
BTC/USD           Bitcoin to Dollar    Bitstamp     $  89.06700K      0.22   22  553ms
BTC/USD           Bitcoin to Dollar    Coinbase     $  89.06769K      0.25   25  261ms
BTC/USD           Bitcoin to Dollar    Gemini       $  89.05753K      0.17   17  787ms
BTC/USD           Bitcoin to Dollar    Kraken       $  89.05310K      0.18   18  226ms
BTC/USDT          Bitcoin to Tether    Binance      ₮  89.19590K      0.65   65  374ms
BTC/USDT          Bitcoin to Tether    Bybit        ₮  89.19105K      0.1    10  467ms
BTC/USDT          Bitcoin to Tether    Huobi        ₮  89.19650K      0.05    5  472ms
BTC/USDT          Bitcoin to Tether    KuCoin       ₮  89.19595K      0.05    5  756ms
BTC/USDT          Bitcoin to Tether    OKX          ₮  89.19965K      0.15   15  759ms

    Coinpair              Value   Sources count    Ok   Time
--  ------------  -------------  ---------------  ----  ------
⇓   BTC/USD       89,067.000000      5 of 5        ✓    787ms
ƒ   BTC/USD(24h)        ▼ 0.25%        N/A         ✓    2.66s
⛓   BTC/USD(och)  89,089.000000      1 of 1        ✓    1.66s
⇓   BTC/USDT      89,195.905000      5 of 5        ✓    759ms

Response time 4.36s

user@host:~$ 
```

This command has many options. you can run `moc_prices_source_check --help` to get help on how to run them.
More information about this CLI tool can be seen [here](docs/cli.md).



## References

* [Source code in Github](https://github.com/money-on-chain/moc_prices_source)
* [Package from Python package index (PyPI)](https://pypi.org/project/moneyonchain-prices-source)



## Requirements

* Python 3.6+ support



## Installation

### From the Python package index (PyPI) 

Run:

```shell
$ pip3 install moneyonchain-prices-source 
```

And then run:

```shell
$ moc_prices_source_check --version
```

To verify that it has been installed correctly

### From source

Download from [Github](https://github.com/money-on-chain/moc_prices_source)

Standing inside the folder, run:

```shell
$ pip3 install -r requirements.txt 
```

For install the dependencies and then run:

```shell
$ pip3 install .
```

Finally run:

```shell
$ moc_prices_source_check --version
```

To verify that it has been installed correctly



## Supported coinpairs and symbols

[Here](docs/supported_coinpairs.md) you can find an [summary of supported coinpairs and symbols](docs/supported_coinpairs.md)

