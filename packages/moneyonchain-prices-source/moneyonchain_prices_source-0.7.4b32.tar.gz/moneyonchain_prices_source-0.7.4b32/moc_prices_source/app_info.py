author = 'Juan S. Bokser'
author_email = 'juan.bokser@moneyonchain.com'
app_name = 'MOC prices source'
description = 'Money on chain price repository and source'
author_user = 'jbokser'
repo_url = "https://github.com/money-on-chain/moc_prices_source"
pypi_url = "https://pypi.org/project/moneyonchain-prices-source"

#######################################
from os.path import abspath as _abs
from os.path import dirname as _dir
with open(_dir(_abs(__file__)) + "/version.txt", "r") as _file:
    version = _file.read().split()[0]
is_beta = 'b' in version or 'beta' in version
app_info = {} # as dict  
for key, value in dict(locals()).items():
    if key[0]!="_" and key not in ['app_info'] :
        app_info[key] = value
