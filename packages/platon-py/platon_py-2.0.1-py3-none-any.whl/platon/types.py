from typing import (
    Any,
    NewType,
    Optional,
    Union,
    Sequence
)
from web3._utils.compat import (
    TypedDict,
)
from hexbytes import (
    HexBytes,
)
from eth_typing import (
    HexStr,
    BlockNumber,
    ChecksumAddress
)

Version = NewType('Version', int)
Nonce = NewType("Nonce", int)
Timestamp = NewType("Timestamp", int)
Von = NewType('Von', int)

FunctionIdentifier = NewType('FunctionIdentifier', int)  # Only used in inner contracts

class CodeData(TypedDict):
    code: int
    message: str
    data: Optional[Any]

# syntax b/c "from" keyword not allowed w/ class construction
TxData = TypedDict("TxData", {
    "blockHash": HexBytes,
    "blockNumber": BlockNumber,
    "chain_id": int,
    "data": Union[bytes, HexStr],
    "from": ChecksumAddress,
    "gas": Von,
    "gasPrice": Von,
    # "maxFeePerGas": Von,
    # "maxPriorityFeePerGas": Von,
    "hash": HexBytes,
    # "input": HexStr,
    "nonce": Nonce,
    "r": HexBytes,
    "s": HexBytes,
    "to": ChecksumAddress,
    "transactionIndex": int,
    "v": int,
    "value": Von,
}, total=False)

class BlockData(TypedDict, total=False):
    baseFeePerGas: Von
    difficulty: int
    extraData: HexBytes
    gasLimit: Von
    gasUsed: Von
    hash: HexBytes
    logsBloom: HexBytes
    miner: ChecksumAddress
    # mixHash: HexBytes
    nonce: HexBytes
    number: BlockNumber
    parentHash: HexBytes
    receiptRoot: HexBytes
    sha3Uncles: HexBytes
    size: int
    stateRoot: HexBytes
    timestamp: Timestamp
    totalDifficulty: int
    # list of tx hashes or of txdatas
    transactions: Union[Sequence[HexBytes], Sequence[TxData]]
    transactionsRoot: HexBytes

BlockQuorumCert = TypedDict("BlockQuorumCert", {
    "blockHash": HexStr,
    "blockIndex": int,
    "blockNumber": int,
    "epoch": int,
    "signature": HexStr,
    "validatorSet": str,
    "viewNumber": int,
}, total=False)

class InnerFn:
    # staking
    staking_createStaking = FunctionIdentifier(1000)
    staking_editStaking = FunctionIdentifier(1001)
    staking_increaseStaking = FunctionIdentifier(1002)
    staking_withdrewStaking = FunctionIdentifier(1003)
    staking_getVerifierList = FunctionIdentifier(1100)
    staking_getValidatorList = FunctionIdentifier(1101)
    staking_getCandidateList = FunctionIdentifier(1102)
    staking_getCandidateInfo = FunctionIdentifier(1105)
    staking_getBlockReward = FunctionIdentifier(1200)
    staking_getStakingReward = FunctionIdentifier(1201)
    staking_getAvgBlockTime = FunctionIdentifier(1202)
    # delegate
    delegate_delegate = FunctionIdentifier(1004)
    delegate_withdrewDelegate = FunctionIdentifier(1005)
    delegate_redeemDelegate = FunctionIdentifier(1006)
    delegate_getDelegateList = FunctionIdentifier(1103)
    delegate_getDelegateInfo = FunctionIdentifier(1104)
    delegate_getDelegateLockInfo = FunctionIdentifier(1106)
    delegate_withdrawDelegateReward = FunctionIdentifier(5000)
    delegate_getDelegateReward = FunctionIdentifier(5100)
    # govern
    govern_submitTextProposal = FunctionIdentifier(2000)
    govern_submitVersionProposal = FunctionIdentifier(2001)
    govern_submitParamProposal = FunctionIdentifier(2002)
    govern_vote = FunctionIdentifier(2003)
    govern_declareVersion = FunctionIdentifier(2004)
    govern_submitCancelProposal = FunctionIdentifier(2005)
    govern_getProposal = FunctionIdentifier(2100)
    govern_getProposalResult = FunctionIdentifier(2101)
    govern_proposalList = FunctionIdentifier(2102)
    govern_getChainVersion = FunctionIdentifier(2103)
    govern_getGovernParam = FunctionIdentifier(2104)
    govern_getProposalVotes = FunctionIdentifier(2105)
    govern_governParamList = FunctionIdentifier(2106)
    # slashing
    slashing_reportDuplicateSign = FunctionIdentifier(3000)
    slashing_checkDuplicateSign = FunctionIdentifier(3001)
    slashing_zeroProduceNodeList = FunctionIdentifier(3002)
    # restricting
    restricting_createRestricting = FunctionIdentifier(4000)
    restricting_getRestrictingInfo = FunctionIdentifier(4100)
