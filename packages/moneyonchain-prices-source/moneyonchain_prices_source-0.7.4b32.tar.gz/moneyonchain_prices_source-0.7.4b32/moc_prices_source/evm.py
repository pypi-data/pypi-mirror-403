from __future__ import annotations
import requests, json
from decimal import Decimal
from dataclasses import dataclass
from typing import Any, List, Optional, Tuple
from eth_utils import keccak, to_checksum_address
from web3 import Web3 as Web3base
from web3 import HTTPProvider
try:
    from eth_abi import decode as abi_decode
except ImportError:
    from eth_abi.abi import decode_abi as abi_decode
try:
    from eth_abi import encode as abi_encode
except ImportError:
    from eth_abi.abi import encode_abi as abi_encode
from urllib.parse import urlparse
from .my_envs import envs



class Web3(Web3base):
    """ Override Original Web3 """

    def is_connected(self) -> bool:
        try:
            return super().is_connected()
        except AttributeError:
            return super().isConnected()

    @staticmethod
    def to_checksum_address(value):
        try:
            return Web3base.to_checksum_address(value)
        except:
            return Web3base.toChecksumAddress(value)


class OneShotHTTPProvider(HTTPProvider):
    def make_request(self, method, params):
        payload = {"jsonrpc": "2.0",
                   "method": method,
                   "params": params,
                   "id": 1}
        headers = {"Content-Type": "application/json",
                   "Connection": "close"}
        with requests.Session() as s:
            resp = s.post(self.endpoint_uri,
                          headers=headers,
                          data=json.dumps(payload))
            resp.raise_for_status()
            return resp.json()


@dataclass(frozen=True)
class FunctionSpecData:
    name: str
    inputs: Tuple[str, ...]
    outputs: Tuple[str, ...]

    @property
    def canonical_sig(self) -> str:
        return f"{self.name}({','.join(self.inputs)})"
    
    @property
    def selector(self) -> bytes:
        return keccak(text=self.canonical_sig)[:4]

    @property
    def as_dict(self) -> dict:
        return {'name': self.name,
                'inputs': self.inputs,
                'outputs': self.outputs,
                'canonical_sig': self.canonical_sig,
                'selector': self.selector}

    def _normalize_arg(self, abi_type: str, value: Any) -> Any:
        t = abi_type.strip()

        if t.endswith("]"):
            if not isinstance(value, (list, tuple)):
                raise TypeError(f"ABI type {t} expects list/tuple")
            base = t[: t.rfind("[")]
            return [self._normalize_arg(base, v) for v in value]

        if t == "address":
            if not isinstance(value, str):
                raise TypeError("address must be hex string")
            return to_checksum_address(value)

        if t == "bool":
            if isinstance(value, bool):
                return value
            if isinstance(value, int):
                return bool(value)
            if isinstance(value, str):
                return value.lower() in {"true", "1", "yes", "y"}
            raise TypeError(f"Cannot coerce {value!r} to bool")

        if t.startswith("uint") or t.startswith("int"):
            if isinstance(value, int):
                return value
            if isinstance(value, str):
                return int(value, 16) if value.startswith("0x") else int(value)
            raise TypeError(f"Cannot coerce {value!r} to int")

        if t == "bytes":
            if isinstance(value, (bytes, bytearray)):
                return bytes(value)
            if isinstance(value, str) and value.startswith("0x"):
                return bytes.fromhex(value[2:])
            raise TypeError(f"Cannot coerce {value!r} to bytes")

        if t.startswith("bytes"):
            if isinstance(value, (bytes, bytearray)):
                return bytes(value)
            if isinstance(value, str) and value.startswith("0x"):
                return bytes.fromhex(value[2:])
            raise TypeError(f"Cannot coerce {value!r} to {t}")

        if t == "string":
            return str(value)

        return value

    def normalize_args(self, *args) -> List[Any]:
        if len(args) != len(self.inputs):
            raise ValueError(
                "Argument count mismatch: "
                f"expected {len(self.inputs)}, got {len(args)}"
            )
        return [self._normalize_arg(t, v) for t, v in zip(self.inputs, args)]

    def encode_args(self, *args) -> bytes:
        norm_args = self.normalize_args(*args)
        return abi_encode(list(self.inputs), norm_args) if self.inputs else b""

    def make_calldata(self, *args) -> bytes:
        return self.selector + self.encode_args(*args)
    
    def __str__(self):
        return f"{self.canonical_sig}({','.join(self.outputs)})"

    def decode_outputs(self, result: bytes) -> Any:
        if not self.outputs:
            return None
        decoded = abi_decode(list(self.outputs), result)
        if len(decoded) == 1:
            return decoded[0]
        return decoded


class FunctionSpec(FunctionSpecData):

    @staticmethod
    def _split_types(type_list: str) -> Tuple[str, ...]:
        s = type_list.strip()
        if not s:
            return ()

        out: List[str] = []
        buf: List[str] = []
        depth = 0
        for ch in s:
            if ch == "," and depth == 0:
                t = "".join(buf).strip()
                if t:
                    out.append(t)
                buf = []
                continue
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            buf.append(ch)

        tail = "".join(buf).strip()
        if tail:
            out.append(tail)
        return tuple(out)

    def __init__(self, fn_spec: str):        
        s = fn_spec.strip()

        i1 = s.find("(")
        if i1 <= 0:
            raise ValueError(f"Invalid fn_spec (missing inputs): {fn_spec!r}")

        name = s[:i1].strip()
        if not name:
            raise ValueError(f"Invalid fn_spec (empty name): {fn_spec!r}")

        depth = 0
        end_inputs = None
        for idx in range(i1, len(s)):
            if s[idx] == "(":
                depth += 1
            elif s[idx] == ")":
                depth -= 1
                if depth == 0:
                    end_inputs = idx
                    break
        if end_inputs is None:
            raise ValueError(f"Invalid fn_spec (unclosed inputs): {fn_spec!r}")

        inputs_str = s[i1 + 1 : end_inputs]
        rest = s[end_inputs + 1 :].strip()

        if not rest.startswith("("):
            raise ValueError(f"Invalid fn_spec (missing outputs): {fn_spec!r}")

        depth = 0
        end_outputs = None
        for idx in range(len(rest)):
            if rest[idx] == "(":
                depth += 1
            elif rest[idx] == ")":
                depth -= 1
                if depth == 0:
                    end_outputs = idx
                    break
        if end_outputs is None:
            raise ValueError(f"Invalid fn_spec (unclosed outputs): {fn_spec!r}")

        outputs_str = rest[1:end_outputs]
        trailing = rest[end_outputs + 1 :].strip()
        if trailing:
            raise ValueError(f"Invalid fn_spec (extra trailing text): {fn_spec!r}")

        super().__init__(
            name=name,
            inputs=self._split_types(inputs_str),
            outputs=self._split_types(outputs_str),
        )

    def __repr__(self):
        return f"{self.__class__.__name__}({repr(str(self))})"


class EVMConnectionError(RuntimeError):
    pass


class EVMNoMulticallDefined(RuntimeError):
    pass


class EVMCallError(RuntimeError):
    pass


class Address(str):

    def __new__(cls, addr: str | int):

        if addr is None:
            raise ValueError('addr is None')
        
        if hasattr(addr, 'address'):
            addr = addr.address

        if isinstance(addr, int):

            addr = hex(addr)[2:]
            addr = addr[-40:]
            addr = "0" * (40-len(addr)) + addr

        else:

            addr = str(addr).strip()

            if addr.startswith('0x'):
                addr = addr[2:]

            try:
                int(addr, 16)
            except:
                raise ValueError('addr is not hexa')

            if len(addr) != 40:
                raise ValueError('addr has less o more than 40 digits')

        addr = '0x' + addr.lower()

        return super().__new__(cls, addr)

    def make_abbreviation(self, sep='…', length=11):                
        length -= len(sep) 
        length -= 2  # 0x
        pre = int((length)/2)
        post = length - pre
        pre += 2  # 0x
        return f"{self[:pre]}{sep}{self[-post:]}"

    @property
    def abbreviation(self):
        return self.make_abbreviation()

class URI(str):

    def __new__(cls, uri: str):

        if uri is None:
            raise ValueError('uri is None')
        
        ok = False
        try:
            data = urlparse(uri)
            ok = all([
                data.scheme,
                data.netloc
            ])
        except Exception:
            pass
        
        if ok:
            return super().__new__(cls, uri)
        else:
            raise ValueError(f"{repr(uri)} is not a valid URI")


class EVM():

    BALANCE_OF = 'balanceOf(address)(uint256)'

    def __init__(self,
                 rpc_uri_or_web3_obj: str | Web3,
                 block_identifier: str | int = 'latest',
                 multicall_addr: Optional[Address] = None):
        if isinstance(rpc_uri_or_web3_obj, str):
            self.web3 = Web3(OneShotHTTPProvider(rpc_uri_or_web3_obj))
        elif isinstance(rpc_uri_or_web3_obj, Web3):
            self.web3 = rpc_uri_or_web3_obj
        else:
            raise ValueError('Invalid RPC URI or Web3 object')
        self.block_identifier = block_identifier
        if multicall_addr is not None:
            self.set_multicall(multicall_addr)

    _multicall = None

    @property
    def multicall(self):
        if self._multicall is None:
            raise EVMNoMulticallDefined(
                'no multicall address defined, use set_multicall')
        return self._multicall
    
    @multicall.setter
    def multicall(self, value: Multicall):
        if not isinstance(value, Multicall):
            raise TypeError('is not a multicall instance')
        self._multicall = value

    def set_multicall(self, addr: Address):
        self.multicall = Multicall(self, addr)
        return self.multicall

    def is_connected(self) -> bool:
        return self.web3.is_connected()
    
    @property
    def block_identifier(self) -> str | int:
        return self._block_identifier

    @block_identifier.setter
    def block_identifier(self, value: str | int ):

        if isinstance(value, str):
            if value.strip().lower() in ['latest', 'last', 'now']:
                self._block_identifier = 'latest'
                return            
            else:
                value = int(value)

        if isinstance(value, int) and value>1:
            self._block_identifier = value
            return
        
        raise ValueError("is not 'latest' or integer > 0")

    @property
    def latest(self) -> bool:
        return self._block_identifier=='latest'

    @property
    def latest_block_number(self) -> int:
        self.connection_check()
        # Fix: backcompatibility with various web3 versions
        try:
            value = self.web3.eth.block_number
        except AttributeError:
            value = self.web3.eth.blockNumber
        return int(value)

    @property
    def gas_price(self) -> int:
        self.connection_check()
        # Fix: backcompatibility with various web3 versions
        try:
            value = self.web3.eth.gas_price
        except AttributeError:
            value = self.web3.eth.gasPrice
        return Decimal(value) / (10**18)

    def connection_check(self):
        if not self.web3.is_connected():
            raise EVMConnectionError(f"Cannot connect to {self.web3.provider}")        

    def call(self,
        contract_address: Address,
        fn_spec: str | FunctionSpec,
        *args: Any,
        block_identifier: Optional[str | int] = None,
        from_address: Optional[Address] = None,
        gas: Optional[int] = None) -> Any:
        """Perform an eth_call"""

        contract_address = to_checksum_address(Address(contract_address))
        
        if from_address:
            from_address = to_checksum_address(Address(from_address))

        self.connection_check()

        if block_identifier is None:
            block_identifier = self.block_identifier  

        if isinstance(fn_spec, str):
            fn_spec = FunctionSpec(fn_spec)
        
        if not isinstance(fn_spec, FunctionSpec):
            raise ValueError("'fn_spec' is not str or FunctionSpec")
        
        tx = {
            "to": contract_address,
            "data": fn_spec.make_calldata(*args),
        }

        if from_address:
            tx["from"] = from_address
        
        if gas:
            tx["gas"] = gas

        try:
            result = self.web3.eth.call(tx, block_identifier=block_identifier)
        except Exception as e:
            raise EVMCallError(f"eth_call failed: {e}") from e

        return fn_spec.decode_outputs(result)


@dataclass(frozen=True)
class Call:
    to: Address
    data: bytes
    
    @property
    def data_as_str(self):
        return f"{self.data.hex()}"

    @property
    def to_as_str(self):
        return f"{to_checksum_address(self.to)}"
    
    @property
    def as_tuple(self):
        return (self.to_as_str, self.data)

    def __repr__(self):
        return (f"Call(to={repr(self.to_as_str)}, "
                f"data={repr(self.data_as_str)})")

    def __str__(self):
        return repr(self)


class Multicall():

    def __init__(self,
                 uri_or_web3_or_evm: str | Web3 | EVM,
                 address: Address):
        if isinstance(uri_or_web3_or_evm, (str, Web3)):
            self.evm = EVM(uri_or_web3_or_evm)
        elif isinstance(uri_or_web3_or_evm, EVM):
            self.evm = uri_or_web3_or_evm
        else:
            raise ValueError('Invalid RPC URI or Web3 object or EVM object')
        self.web3: Web3 = self.evm.web3
        self.address = Address(address)
        self.clear_calls()

    def clear_calls(self):
        self._already_been_executed_once = {}
        self._calls = {}
        self._last_id = 0

    def _raw_multicall(self, *args, block_identifier: Optional[str | int] = None):
        
        abi = [
            {
                "inputs": [
                    {
                        "components": [
                            {
                                "internalType": "address",
                                "name": "target",
                                "type": "address"
                            },
                            {
                                "internalType": "bytes",
                                "name": "callData",
                                "type": "bytes"
                            }
                        ],
                        "internalType": "struct Multicall2.Call[]",
                        "name": "calls",
                        "type": "tuple[]"
                    }
                ],
                "name": "aggregate",
                "outputs": [
                    {
                        "internalType": "uint256",
                        "name": "blockNumber",
                        "type": "uint256"
                    },
                    {
                        "internalType": "bytes[]",
                        "name": "returnData",
                        "type": "bytes[]"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "components": [
                            {
                                "internalType": "address",
                                "name": "target",
                                "type": "address"
                            },
                            {
                                "internalType": "bytes",
                                "name": "callData",
                                "type": "bytes"
                            }
                        ],
                        "internalType": "struct Multicall2.Call[]",
                        "name": "calls",
                        "type": "tuple[]"
                    }
                ],
                "name": "blockAndAggregate",
                "outputs": [
                    {
                        "internalType": "uint256",
                        "name": "blockNumber",
                        "type": "uint256"
                    },
                    {
                        "internalType": "bytes32",
                        "name": "blockHash",
                        "type": "bytes32"
                    },
                    {
                        "components": [
                            {
                                "internalType": "bool",
                                "name": "success",
                                "type": "bool"
                            },
                            {
                                "internalType": "bytes",
                                "name": "returnData",
                                "type": "bytes"
                            }
                        ],
                        "internalType": "struct Multicall2.Result[]",
                        "name": "returnData",
                        "type": "tuple[]"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "uint256",
                        "name": "blockNumber",
                        "type": "uint256"
                    }
                ],
                "name": "getBlockHash",
                "outputs": [
                    {
                        "internalType": "bytes32",
                        "name": "blockHash",
                        "type": "bytes32"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "getBlockNumber",
                "outputs": [
                    {
                        "internalType": "uint256",
                        "name": "blockNumber",
                        "type": "uint256"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "getCurrentBlockCoinbase",
                "outputs": [
                    {
                        "internalType": "address",
                        "name": "coinbase",
                        "type": "address"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "getCurrentBlockDifficulty",
                "outputs": [
                    {
                        "internalType": "uint256",
                        "name": "difficulty",
                        "type": "uint256"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "getCurrentBlockGasLimit",
                "outputs": [
                    {
                        "internalType": "uint256",
                        "name": "gaslimit",
                        "type": "uint256"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "getCurrentBlockTimestamp",
                "outputs": [
                    {
                        "internalType": "uint256",
                        "name": "timestamp",
                        "type": "uint256"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "address",
                        "name": "addr",
                        "type": "address"
                    }
                ],
                "name": "getEthBalance",
                "outputs": [
                    {
                        "internalType": "uint256",
                        "name": "balance",
                        "type": "uint256"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "getLastBlockHash",
                "outputs": [
                    {
                        "internalType": "bytes32",
                        "name": "blockHash",
                        "type": "bytes32"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "bool",
                        "name": "requireSuccess",
                        "type": "bool"
                    },
                    {
                        "components": [
                            {
                                "internalType": "address",
                                "name": "target",
                                "type": "address"
                            },
                            {
                                "internalType": "bytes",
                                "name": "callData",
                                "type": "bytes"
                            }
                        ],
                        "internalType": "struct Multicall2.Call[]",
                        "name": "calls",
                        "type": "tuple[]"
                    }
                ],
                "name": "tryAggregate",
                "outputs": [
                    {
                        "components": [
                            {
                                "internalType": "bool",
                                "name": "success",
                                "type": "bool"
                            },
                            {
                                "internalType": "bytes",
                                "name": "returnData",
                                "type": "bytes"
                            }
                        ],
                        "internalType": "struct Multicall2.Result[]",
                        "name": "returnData",
                        "type": "tuple[]"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "bool",
                        "name": "requireSuccess",
                        "type": "bool"
                    },
                    {
                        "components": [
                            {
                                "internalType": "address",
                                "name": "target",
                                "type": "address"
                            },
                            {
                                "internalType": "bytes",
                                "name": "callData",
                                "type": "bytes"
                            }
                        ],
                        "internalType": "struct Multicall2.Call[]",
                        "name": "calls",
                        "type": "tuple[]"
                    }
                ],
                "name": "tryBlockAndAggregate",
                "outputs": [
                    {
                        "internalType": "uint256",
                        "name": "blockNumber",
                        "type": "uint256"
                    },
                    {
                        "internalType": "bytes32",
                        "name": "blockHash",
                        "type": "bytes32"
                    },
                    {
                        "components": [
                            {
                                "internalType": "bool",
                                "name": "success",
                                "type": "bool"
                            },
                            {
                                "internalType": "bytes",
                                "name": "returnData",
                                "type": "bytes"
                            }
                        ],
                        "internalType": "struct Multicall2.Result[]",
                        "name": "returnData",
                        "type": "tuple[]"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
        fnc_name = 'tryBlockAndAggregate'

        if block_identifier is None:
            block_identifier = self.evm.block_identifier

        contract = self.web3.eth.contract(
            address = to_checksum_address(self.address),
            abi = abi)
        
        fnc = getattr(contract.functions, fnc_name)

        return fnc(False, args).call(block_identifier=block_identifier)[2]

    def _make_call(self,
        contract_address: Address,
        fn_spec: str | FunctionSpec,
        *args: Any) -> Call:

        contract_address = to_checksum_address(Address(contract_address))

        if isinstance(fn_spec, str):
            fn_spec = FunctionSpec(fn_spec)
        
        if not isinstance(fn_spec, FunctionSpec):
            raise ValueError("'fn_spec' is not str or FunctionSpec")
        
        return Call(to = contract_address,
                    data = fn_spec.make_calldata(*args))

    def _get_call_from_id(self, i: int) -> Call:
        for key, value in self._calls.items():
            if value['id']==i:
                return key
        raise IndexError()

    def add_call(self,
        contract_address: Address,
        fn_spec: str | FunctionSpec,
        *args: Any) -> int:

        call = self._make_call(contract_address, fn_spec, *args)
        
        if call in self._calls:
            id_ = self._calls[call]['id']
        else:
            self._last_id += 1
            id_ = self._last_id
            if isinstance(fn_spec, str):
                fn_spec = FunctionSpec(fn_spec)
            self._calls[call] = {
                    'id': id_,
                    'data': {None: None},
                    'fn_spec': fn_spec
                }

        return id_

    def _get_call(self, *args: Any) -> Call:
        if len(args)==1:
            arg = args[0]
            if isinstance(arg, int):
                i = arg
                return self._get_call(self._get_call_from_id(i))
            if isinstance(arg, Call):
                call = arg
                if call not in self._calls:
                    raise IndexError()
                return call
        contract_address: Address
        fn_spec: str | FunctionSpec
        contract_address, fn_spec, *args = args
        call = self._make_call(contract_address, fn_spec, *args)
        return self._get_call(call)
        
    def remove_call(self, *args: Any) -> None:
        call = self._get_call(*args)
        del self._calls[call]

    def get_call(self, *args: Any, namespace: Optional[str] = None) -> Any:
        call = self._get_call(*args)
        return self._calls[call]['data'][namespace]

    def _run(self,
             block_identifier: Optional[str | int] = None,
             namespace: Optional[str] = None):

        if block_identifier is None:
            block_identifier = self.evm.block_identifier

        calls_items = [ (k, v) for (k, v) in self._calls.items()]

        args = [ k.as_tuple for (k, v) in calls_items]

        raw = self._raw_multicall(*args, block_identifier=block_identifier)

        for (call, extra), (ok, raw_result) in zip(calls_items, raw):
            result = None
            if ok:
                fn_spec = extra['fn_spec']
                result = fn_spec.decode_outputs(raw_result)
            self._calls[call]['data'][namespace] = result

    def reset_executed_once(self, namespace: Optional[str] = None):
        self._already_been_executed_once[namespace] = False   

    def __call__(self,
                 only_first_time = False,
                 block_identifier: Optional[str | int] = None,
                 namespace: Optional[str] = None):
        if not(only_first_time and self._already_been_executed_once.get(
            namespace, False)):
            if block_identifier is None:
                block_identifier = self.evm.block_identifier
            if len(self):
                self._run(block_identifier = block_identifier,
                          namespace = namespace)
                self._already_been_executed_once[namespace] = True
        return len(self)
    
    def run(self,
            block_identifier: Optional[str | int] = None,
            namespace: Optional[str] = None):
        return self(block_identifier = block_identifier,
                    namespace = namespace)
    
    def run_only_first_time(self,
                            block_identifier: Optional[str | int] = None,
                            namespace: Optional[str] = None):
        return self(only_first_time = True,
                    block_identifier = block_identifier,
                    namespace = namespace)

    def __len__(self):
        return len(self._calls)

    def __bool__(self):
        if len(self)==0:
            return False
        return self._already_been_executed_once.get(None, False)


def get_addr_env(env_name: str, default_addr:str) -> str:
    return envs(env_name, Address(default_addr), cast=Address)


def get_uri_env(env_name: str, default_addr: Optional[str] = '') -> str:
    return envs(env_name, default_addr, cast=URI)


def get_node_rpc_uri_env(env_name: str = 'NODE_RPC_URI',
                         default_uri: str = 'rootstock') -> str:
    return envs(env_name, default_uri,
        cast=URI,
        alias={
            'main': 'mainnet',
            'mainnet': 'rootstock',
            'rootstock': 'https://public-node.rsk.co',
            'rootstock_mainnet': 'rootstock',
            'rsk': 'rootstock',
            'rsk_mainnet': 'rootstock',
            'test': 'testnet',
            'testnet': 'rootstock_testnet',
            'rootstock_testnet': 'https://public-node.testnet.rsk.co',
            'rsk_testnet': 'rootstock_testnet'
            })


def get_multicall_addr_env(env_name: str = 'MULTICALL_ADDR',
                         default_addr: str = 'rootstock') -> str:
    return envs(env_name, default_addr,
        cast=Address,
        alias={
            'main': 'mainnet',
            'mainnet': 'rootstock',
            'rootstock': '0x8f344c3b2a02a801c24635f594c5652c8a2eb02a',
            'rootstock_mainnet': 'rootstock',
            'rsk': 'rootstock',
            'rsk_mainnet': 'rootstock',
            'test': 'testnet',
            'testnet': 'rootstock_testnet',
            'rootstock_testnet': '0xaf7be1ef9537018feda5397d9e3bb9a1e4e27ac8',
            'rsk_testnet': 'rootstock_testnet'
            })
