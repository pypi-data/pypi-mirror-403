"""
DeFiStream Python Client

Official Python client for the DeFiStream API - access historical
DeFi events from 45+ EVM networks.

Example:
    >>> from defistream import DeFiStream
    >>> client = DeFiStream(api_key="dsk_...")
    >>>
    >>> # Builder pattern
    >>> query = client.erc20.transfers("USDT").network("ETH").start_block(24000000).end_block(24100000)
    >>> transfers = query.as_dict()
    >>>
    >>> # Save to file
    >>> query.to_csv_file("transfers.csv")
"""

from .client import AsyncDeFiStream, DeFiStream
from .exceptions import (
    AuthenticationError,
    DeFiStreamError,
    NotFoundError,
    QuotaExceededError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from .models import (
    AAVEBorrowEvent,
    AAVEDepositEvent,
    AAVELiquidationEvent,
    AAVERepayEvent,
    AAVEWithdrawEvent,
    ERC20ApprovalEvent,
    ERC20TransferEvent,
    EventBase,
    LidoDepositEvent,
    LidoWithdrawEvent,
    NativeTransferEvent,
    ResponseMetadata,
    UniswapBurnEvent,
    UniswapMintEvent,
    UniswapSwapEvent,
)
from .query import AsyncQueryBuilder, QueryBuilder

__version__ = "0.1.0"

__all__ = [
    # Clients
    "DeFiStream",
    "AsyncDeFiStream",
    # Query builders
    "QueryBuilder",
    "AsyncQueryBuilder",
    # Exceptions
    "DeFiStreamError",
    "AuthenticationError",
    "QuotaExceededError",
    "RateLimitError",
    "ValidationError",
    "NotFoundError",
    "ServerError",
    # Models
    "EventBase",
    "ResponseMetadata",
    "ERC20TransferEvent",
    "ERC20ApprovalEvent",
    "NativeTransferEvent",
    "AAVEDepositEvent",
    "AAVEWithdrawEvent",
    "AAVEBorrowEvent",
    "AAVERepayEvent",
    "AAVELiquidationEvent",
    "UniswapSwapEvent",
    "UniswapMintEvent",
    "UniswapBurnEvent",
    "LidoDepositEvent",
    "LidoWithdrawEvent",
]
