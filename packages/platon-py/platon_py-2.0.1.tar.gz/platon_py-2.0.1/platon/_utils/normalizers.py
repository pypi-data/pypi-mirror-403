import functools
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Optional,
    Tuple,
)
from eth_typing import (
    ChecksumAddress,
    TypeStr,
)
from eth_utils import (
    to_checksum_address,
)
from eth_utils.address import (
    is_binary_address,
)
from web3._utils.validation import (
    validate_address,
)
from web3.types import (  # noqa: F401
    ABI,
    ABIEvent,
    ABIFunction,
)

if TYPE_CHECKING:
    from platon import Web3  # noqa: F401

def implicitly_identity(
    to_wrap: Callable[[TypeStr, Any], Any]
) -> Callable[[TypeStr, Any], Tuple[TypeStr, Any]]:
    @functools.wraps(to_wrap)
    def wrapper(type_str: TypeStr, data: Any) -> Tuple[TypeStr, Any]:
        modified = to_wrap(type_str, data)
        if modified is None:
            return type_str, data
        else:
            return modified
    return wrapper

@implicitly_identity
def abi_address_to_hex(type_str: TypeStr, data: Any) -> Optional[Tuple[TypeStr, ChecksumAddress]]:
    if type_str == 'address' and data:
        validate_address(data)
        if is_binary_address(data):
            return type_str, to_checksum_address(data)
    return None