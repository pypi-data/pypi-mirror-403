import decimal
from eth_abi.codec import (
    ABICodec,
)
from eth_utils import (
    add_0x_prefix,
    apply_to_return_value,
    from_wei,
    is_address,
    is_checksum_address,
    keccak as eth_utils_keccak,
    remove_0x_prefix,
    to_bytes,
    to_checksum_address,
    to_int,
    to_text,
    to_wei,
)
from functools import (
    wraps,
)
from hexbytes import (
    HexBytes,
)
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Sequence,
    TYPE_CHECKING,
    Union,
    cast,
)

from eth_typing import (
    AnyAddress,
    ChecksumAddress,
    HexStr,
    Primitives,
)
from eth_typing.abi import TypeStr
from eth_utils import (
    combomethod,
)

from ens import ENS
from web3._utils.abi import (
    build_default_registry,
    build_strict_registry,
    map_abi_data,
)
from web3._utils.decorators import (
    deprecated_for,
)
from web3._utils.empty import (
    empty,
)
from web3._utils.encoding import (
    hex_encode_abi_type,
    to_hex,
    to_json,
)
from web3._utils.rpc_abi import (
    RPC,
)
from web3._utils.module import (
    attach_modules,
)
from web3._utils.normalizers import (
    abi_ens_resolver,
)

from platon._utils.delegate import (
    Delegate,
)
from platon.debug import (
    Debug,
)
from platon.pip import (
    Pip,
)
from platon.restricting import (
    Restricting,
)
from platon._utils.slashing import (
    Slashing,
)
from platon._utils.staking import (
    Staking,
)
from platon.eth import (
    Eth,
)
from platon.node import (
    Node,
    Admin,
    Miner,
    Personal,
    TxPool,
)
from web3.iban import (
    Iban,
)
from web3.manager import (
    RequestManager as DefaultRequestManager,
)
from web3.net import (
    Net,
)
from platon.ppos import Ppos
from web3.providers import (
    BaseProvider, AutoProvider,
)
from web3.providers.eth_tester import (
    EthereumTesterProvider,
)
from web3.providers.ipc import (
    IPCProvider,
)
from web3.providers.async_rpc import (
    AsyncHTTPProvider,
)
from web3.providers.rpc import (
    HTTPProvider,
)
from web3.providers.websocket import (
    WebsocketProvider,
)
from web3.types import (
    MiddlewareOnion,
    Wei,
)
from web3.version import (
    Version,
)

if TYPE_CHECKING:
    from web3.pm import PM


def get_default_modules() -> Dict[str, Sequence[Any]]:
    return {
        "platon": (Eth,),
        "eth": (Eth,),
        "net": (Net,),
        "version": (Version,),
        "restricting": (Restricting,),
        "ppos": (Ppos, {
            "staking": (Staking,),
            "delegate": (Delegate,),
            "slashing": (Slashing, ),
        }),
        "pip": (Pip, ),
        "node": (Node, {
            "admin": (Admin,),
            "miner": (Miner,),
            "personal": (Personal,),
            "txpool": (TxPool,),
        }),
        "debug": (Debug, ),
    }


class Web3:
    # Providers
    HTTPProvider = HTTPProvider
    IPCProvider = IPCProvider
    EthereumTesterProvider = EthereumTesterProvider
    WebsocketProvider = WebsocketProvider
    AsyncHTTPProvider = AsyncHTTPProvider

    # Managers
    RequestManager = DefaultRequestManager

    # Iban
    Iban = Iban

    # Encoding and Decoding
    @staticmethod
    @wraps(to_bytes)
    def toBytes(
        primitive: Primitives = None, hexstr: HexStr = None, text: str = None
    ) -> bytes:
        return to_bytes(primitive, hexstr, text)

    @staticmethod
    @wraps(to_int)
    def toInt(
        primitive: Primitives = None, hexstr: HexStr = None, text: str = None
    ) -> int:
        return to_int(primitive, hexstr, text)

    @staticmethod
    @wraps(to_hex)
    def toHex(
        primitive: Primitives = None, hexstr: HexStr = None, text: str = None
    ) -> HexStr:
        return to_hex(primitive, hexstr, text)

    @staticmethod
    @wraps(to_text)
    def toText(
        primitive: Primitives = None, hexstr: HexStr = None, text: str = None
    ) -> str:
        return to_text(primitive, hexstr, text)

    @staticmethod
    @wraps(to_json)
    def toJSON(obj: Dict[Any, Any]) -> str:
        return to_json(obj)

    # Currency Utility
    @staticmethod
    @wraps(to_wei)
    def toWei(number: Union[int, float, str, decimal.Decimal], unit: str) -> Wei:
        return cast(Wei, to_wei(number, unit))

    @staticmethod
    @wraps(from_wei)
    def fromWei(number: int, unit: str) -> Union[int, decimal.Decimal]:
        return from_wei(number, unit)

    # Address Utility
    @staticmethod
    @wraps(is_address)
    def isAddress(value: Any) -> bool:
        return is_address(value)

    @staticmethod
    @wraps(is_checksum_address)
    def is_checksum_address(value: Any) -> bool:
        return is_checksum_address(value)

    @staticmethod
    @wraps(to_checksum_address)
    def to_checksum_address(value: Union[AnyAddress, str, bytes]) -> ChecksumAddress:
        return to_checksum_address(value)

    # mypy Types
    platon: Eth
    eth: Eth
    net: Net
    version: Version
    restricting: Restricting
    ppos: Ppos
    pip: Pip
    node: Node
    # parity: Parity
    debug: Debug

    def __init__(
            self,
            provider: Optional[BaseProvider] = None,
            middlewares: Optional[Sequence[Any]] = None,
            modules: Optional[Dict[str, Sequence[Any]]] = None,
            ens: ENS = cast(ENS, empty),
            chain_id: int = None,  # This value is required for versions earlier than 0.16.0
    ) -> None:
        if provider is None:
            provider = AutoProvider()

        self.manager = self.RequestManager(self, provider, middlewares)
        # this codec gets used in the module initialization,
        # so it needs to come before attach_modules
        self.codec = ABICodec(build_default_registry())

        if modules is None:
            modules = get_default_modules()

        attach_modules(self, modules)

        self.ens = ens

        self._chain_id = chain_id

    @property
    def chain_id(self):
        if self._chain_id is None:
            self._chain_id = self.platon.chain_id

        return self._chain_id

    @property
    def middleware_onion(self) -> MiddlewareOnion:
        return self.manager.middleware_onion

    @property
    def provider(self) -> BaseProvider:
        return self.manager.provider

    @provider.setter
    def provider(self, provider: BaseProvider) -> None:
        self.manager.provider = provider

    @property
    def clientVersion(self) -> str:
        return self.manager.request_blocking(RPC.web3_clientVersion, [])

    @property
    def api(self) -> str:
        from web3 import __version__
        return __version__

    @staticmethod
    @deprecated_for("keccak")
    @apply_to_return_value(HexBytes)
    def sha3(primitive: Optional[Primitives] = None, text: Optional[str] = None,
             hexstr: Optional[HexStr] = None) -> bytes:
        return Web3.keccak(primitive, text, hexstr)

    @staticmethod
    @apply_to_return_value(HexBytes)
    def keccak(primitive: Optional[Primitives] = None, text: Optional[str] = None,
               hexstr: Optional[HexStr] = None) -> bytes:
        if isinstance(primitive, (bytes, int, type(None))):
            input_bytes = to_bytes(primitive, hexstr=hexstr, text=text)
            return eth_utils_keccak(input_bytes)

        raise TypeError(
            "You called keccak with first arg %r and keywords %r. You must call it with one of "
            "these approaches: keccak(text='txt'), keccak(hexstr='0x747874'), "
            "keccak(b'\\x74\\x78\\x74'), or keccak(0x747874)." % (
                primitive,
                {'text': text, 'hexstr': hexstr}
            )
        )

    @combomethod
    @deprecated_for("solidityKeccak")
    def soliditySha3(cls, abi_types: List[TypeStr], values: List[Any]) -> bytes:
        return cls.solidityKeccak(abi_types, values)

    @combomethod
    def solidityKeccak(cls, abi_types: List[TypeStr], values: List[Any]) -> bytes:
        """
        Executes keccak256 exactly as Solidity does.
        Takes list of abi_types as inputs -- `[uint24, int8[], bool]`
        and list of corresponding values  -- `[20, [-1, 5, 0], True]`
        """
        if len(abi_types) != len(values):
            raise ValueError(
                "Length mismatch between provided abi types and values.  Got "
                "{0} types and {1} values.".format(len(abi_types), len(values))
            )

        if isinstance(cls, type):
            w3 = None
        else:
            w3 = cls
        normalized_values = map_abi_data([abi_ens_resolver(w3)], abi_types, values)

        hex_string = add_0x_prefix(HexStr(''.join(
            remove_0x_prefix(hex_encode_abi_type(abi_type, value))
            for abi_type, value
            in zip(abi_types, normalized_values)
        )))
        return cls.keccak(hexstr=hex_string)

    def isConnected(self) -> bool:
        return self.provider.isConnected()

    def is_encodable(self, _type: TypeStr, value: Any) -> bool:
        return self.codec.is_encodable(_type, value)

    @property
    def ens(self) -> ENS:
        if self._ens is cast(ENS, empty):
            return ENS.fromWeb3(self)
        else:
            return self._ens

    @ens.setter
    def ens(self, new_ens: ENS) -> None:
        self._ens = new_ens

    @property
    def pm(self) -> "PM":
        if hasattr(self, '_pm'):
            # ignored b/c property is dynamically set via enable_unstable_package_management_api
            return self._pm  # type: ignore
        else:
            raise AttributeError(
                "The Package Management feature is disabled by default until "
                "its API stabilizes. To use these features, please enable them by running "
                "`w3.enable_unstable_package_management_api()` and try again."
            )

    def enable_unstable_package_management_api(self) -> None:
        from web3.pm import PM
        if not hasattr(self, '_pm'):
            attach_modules(self, {'_pm': (PM,)})

    def enable_strict_bytes_type_checking(self) -> None:
        self.codec = ABICodec(build_strict_registry())
