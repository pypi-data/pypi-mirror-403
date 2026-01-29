"""Pydantic models for DeFiStream API responses."""

from typing import Any, Literal
from pydantic import BaseModel, Field


class ResponseMetadata(BaseModel):
    """Metadata from API response headers."""

    rate_limit: int | None = None
    quota_remaining: int | None = None
    request_cost: int | None = None


class EventBase(BaseModel):
    """Base model for all events."""

    block_number: int
    time: str | None = None
    # Verbose fields (only present when verbose=true)
    name: str | None = None
    network: str | None = None
    tx_id: str | None = None
    tx_hash: str | None = None
    log_index: int | None = None


class ERC20TransferEvent(EventBase):
    """ERC20 Transfer event."""

    sender: str = Field(alias="from_address", default="")
    receiver: str = Field(alias="to_address", default="")
    amount: float = 0.0
    token_address: str | None = None
    token_symbol: str | None = None

    model_config = {"populate_by_name": True}


class ERC20ApprovalEvent(EventBase):
    """ERC20 Approval event."""

    owner: str = ""
    spender: str = ""
    amount: float = 0.0
    token_address: str | None = None
    token_symbol: str | None = None


class NativeTransferEvent(EventBase):
    """Native token (ETH/MATIC/etc) transfer event."""

    sender: str = ""
    receiver: str = ""
    amount: float = 0.0


class AAVEDepositEvent(EventBase):
    """AAVE V3 Supply/Deposit event."""

    user: str = ""
    reserve: str = ""
    amount: float = 0.0
    on_behalf_of: str | None = None


class AAVEWithdrawEvent(EventBase):
    """AAVE V3 Withdraw event."""

    user: str = ""
    reserve: str = ""
    amount: float = 0.0
    to: str | None = None


class AAVEBorrowEvent(EventBase):
    """AAVE V3 Borrow event."""

    user: str = ""
    reserve: str = ""
    amount: float = 0.0
    interest_rate_mode: int | None = None
    borrow_rate: float | None = None
    on_behalf_of: str | None = None


class AAVERepayEvent(EventBase):
    """AAVE V3 Repay event."""

    user: str = ""
    reserve: str = ""
    amount: float = 0.0
    repayer: str | None = None
    use_a_tokens: bool | None = None


class AAVELiquidationEvent(EventBase):
    """AAVE V3 Liquidation event."""

    liquidator: str = ""
    user: str = ""
    collateral_asset: str = ""
    debt_asset: str = ""
    debt_to_cover: float = 0.0
    liquidated_collateral_amount: float = 0.0
    receive_a_token: bool | None = None


class UniswapSwapEvent(EventBase):
    """Uniswap V3 Swap event."""

    pool: str = ""
    sender: str = ""
    recipient: str = ""
    amount0: float = 0.0
    amount1: float = 0.0
    sqrt_price_x96: int | None = None
    liquidity: int | None = None
    tick: int | None = None


class UniswapMintEvent(EventBase):
    """Uniswap V3 Mint (add liquidity) event."""

    pool: str = ""
    owner: str = ""
    tick_lower: int = 0
    tick_upper: int = 0
    amount: int = 0
    amount0: float = 0.0
    amount1: float = 0.0


class UniswapBurnEvent(EventBase):
    """Uniswap V3 Burn (remove liquidity) event."""

    pool: str = ""
    owner: str = ""
    tick_lower: int = 0
    tick_upper: int = 0
    amount: int = 0
    amount0: float = 0.0
    amount1: float = 0.0


class LidoDepositEvent(EventBase):
    """Lido stETH deposit event."""

    sender: str = ""
    amount: float = 0.0
    shares: float = 0.0


class LidoWithdrawEvent(EventBase):
    """Lido stETH withdrawal event."""

    owner: str = ""
    request_id: int = 0
    amount: float = 0.0


class EventsResponse(BaseModel):
    """Standard events API response."""

    status: Literal["success", "error"]
    events: list[dict[str, Any]] = []
    count: int = 0
    error: str | None = None


class DecodersResponse(BaseModel):
    """Response from /decoders endpoint."""

    decoders: list[str] = []
