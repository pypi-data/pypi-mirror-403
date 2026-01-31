from typing import (
    Callable,
)

from eth_typing import HexStr
from web3.method import (
    default_root_munger,
)
from platon.method import (
    Method
)
from web3.module import (
    Module,
)
from web3.types import (
    RPCEndpoint,
)


class Debug(Module):
    economic_config: Method[Callable[[], str]] = Method(RPCEndpoint("debug_economicConfig"))
    get_wait_slashing_node_list: Method[Callable[[], str]] = Method(RPCEndpoint("debug_getWaitSlashingNodeList"))
    get_bad_blocks: Method[Callable[[], str]] = Method(RPCEndpoint("debug_getBadBlocks"))
    get_validator_by_blockNumber: Method[Callable[[int], str]] = Method(
        RPCEndpoint("debug_getValidatorByBlockNumber"),
        mungers=[default_root_munger],
    )

    accountRange: Method[Callable[[HexStr, int], str]] = Method(
        RPCEndpoint("debug_accountRange"),
        mungers=[default_root_munger],
    )

    chaindbProperty: Method[Callable[[str], str]] = Method(
        RPCEndpoint("debug_chaindbProperty"),
        mungers=[default_root_munger],
    )
