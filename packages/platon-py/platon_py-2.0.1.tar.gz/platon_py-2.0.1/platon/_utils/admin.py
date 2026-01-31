from typing import (
    Callable,
)

from web3._utils.rpc_abi import (
    RPC,
)
from web3.method import (
    # Method,
    default_root_munger,
)

from platon.method import (
    Method
)

from web3.types import (
    EnodeURI,
    RPCEndpoint
)

rmeove_peer: Method[Callable[[EnodeURI], bool]] = Method(
    RPCEndpoint("admin_removePeer"),
    mungers=[default_root_munger],
)

import_chain: Method[Callable[[str], str]] = Method(
    RPCEndpoint("admin_importChain"),
    mungers=[default_root_munger],
)

export_chain: Method[Callable[[str, int, int], str]] = Method(
    RPCEndpoint("admin_exportChain"),
    mungers=[default_root_munger],
)

get_program_version: Method[Callable[[], str]] = Method(
    RPCEndpoint("admin_getProgramVersion"),
    mungers=None,
)

get_schnorr_NIZK_prove: Method[Callable[[], str]] = Method(
    RPCEndpoint("admin_getSchnorrNIZKProve"),
    mungers=None,
)
