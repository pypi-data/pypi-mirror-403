from ..namespaces import AutoNamespace
from ..evm import EVM, Address
from ..evm import get_multicall_addr_env, get_node_rpc_uri_env, get_addr_env
from ..my_envs import envs
from ..my_logging import get_logger 


chain = AutoNamespace()

with chain.rsk_mainnet as network:
    network.name = "RSK Mainnet"
    network.enabled = envs('RSK_MAINNET_ENABLED', True, bool)
    if network.enabled:
        with network.env.node_rpc_uri as env:
            env.name = 'NODE_RPC_URI'
            env.default = 'rootstock'
        with network.env.multicall_addr as env:
            env.name = 'MULTICALL_ADDR'
            env.default = 'rootstock'
        with network.env.btc_usd_oracle_addr as env:
            env.name = 'BTC_USD_ORACLE_ADDR'
            env.default = '0xe2927A0620b82A66D67F678FC9b826B0E01B1bFD'
        with network.env.mcg_addr as env:
            env.name = 'MULTI_COLLATERAL_GUARD_ADDR'
            env.default = Address(0)

with chain.rsk_testnet as network:
    network.name = "RSK Testnet"
    network.enabled = envs('RSK_TESTNET_ENABLED', True, bool)
    if network.enabled:
        with network.env.node_rpc_uri as env:
            env.name = 'NODE_RPC_URI_TESTNET'
            env.default = 'rootstock_testnet'
        with network.env.multicall_addr as env:
            env.name = 'MULTICALL_ADDR_TESTNET'
            env.default = 'rootstock_testnet'
        with network.env.mcg_addr as env:
            env.name = 'MULTI_COLLATERAL_GUARD_TESTNET_ADDR'
            env.default = Address(0)

# Initialize EVM instances and other network-specific settings

logger = get_logger(__name__)

with chain.rsk_mainnet as network:
    if network.enabled:
        with network.env.btc_usd_oracle_addr as env:
            network.btc_usd_oracle_addr = get_addr_env(env.name, env.default)
            if network.btc_usd_oracle_addr == Address(0):
                logger.warning("%s BTC/USD oracle is not set. You can set the"
                               " %s environment variable to correct that.",
                               network.name, env.name)

for network in chain:
    if network.enabled:
        with network.env as env:
            network.multicall_addr = get_multicall_addr_env(
                env_name = env.multicall_addr.name,
                default_addr = env.multicall_addr.default)
            if network.multicall_addr == Address(0):
                logger.warning("%s MultiCall address is not set. You can set "
                               "the %s environment variable to correct that.",
                               network.name, env.multicall_addr.name)
            network.node_rpc_uri = get_node_rpc_uri_env(
                env_name = env.node_rpc_uri.name,
                default_uri = env.node_rpc_uri.default)
        network.evm = EVM(network.node_rpc_uri,
                        multicall_addr=network.multicall_addr)
        network.mcg_addr = get_addr_env(
            env.mcg_addr.name,
            env.mcg_addr.default)
        if network.mcg_addr == Address(0):
            logger.warning("%s MultiCollateralGuard address is not set. You "
                           "can set the %s environment variable to correct "
                           "that.", network.name, env.mcg_addr.name)

chain.freeze()
