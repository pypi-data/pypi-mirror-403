"""Protocol-specific API clients with builder pattern."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .query import QueryBuilder, AsyncQueryBuilder

if TYPE_CHECKING:
    from .client import BaseClient


class ERC20Protocol:
    """ERC20 token events with builder pattern."""

    def __init__(self, client: "BaseClient"):
        self._client = client

    def transfers(self, token: str | None = None) -> QueryBuilder:
        """
        Start a query for ERC20 transfer events.

        Args:
            token: Optional token symbol (USDT, USDC, WETH, etc.)

        Returns:
            QueryBuilder for chaining filters

        Example:
            query = client.erc20.transfers("USDT").network("ETH").start_block(24000000).end_block(24100000)
            df = query.as_pandas()
        """
        params = {"token": token} if token else {}
        return QueryBuilder(self._client, "/erc20/events/transfer", params)

    def approvals(self, token: str | None = None) -> QueryBuilder:
        """
        Start a query for ERC20 approval events.

        Args:
            token: Optional token symbol

        Returns:
            QueryBuilder for chaining filters
        """
        params = {"token": token} if token else {}
        return QueryBuilder(self._client, "/erc20/events/approval", params)


class NativeTokenProtocol:
    """Native token (ETH, MATIC, BNB, etc.) events with builder pattern."""

    def __init__(self, client: "BaseClient"):
        self._client = client

    def transfers(self) -> QueryBuilder:
        """
        Start a query for native token transfer events.

        Returns:
            QueryBuilder for chaining filters

        Example:
            query = client.native_token.transfers().network("ETH").start_block(24000000).end_block(24100000)
            transfers = query.min_amount(1.0).as_dict()
        """
        return QueryBuilder(self._client, "/native_token/events/transfer")


class AAVEProtocol:
    """AAVE V3 lending protocol events with builder pattern."""

    def __init__(self, client: "BaseClient"):
        self._client = client

    def deposits(self) -> QueryBuilder:
        """Start a query for AAVE deposit/supply events."""
        return QueryBuilder(self._client, "/aave/events/deposit")

    def withdrawals(self) -> QueryBuilder:
        """Start a query for AAVE withdrawal events."""
        return QueryBuilder(self._client, "/aave/events/withdraw")

    def borrows(self) -> QueryBuilder:
        """Start a query for AAVE borrow events."""
        return QueryBuilder(self._client, "/aave/events/borrow")

    def repays(self) -> QueryBuilder:
        """Start a query for AAVE repay events."""
        return QueryBuilder(self._client, "/aave/events/repay")

    def liquidations(self) -> QueryBuilder:
        """Start a query for AAVE liquidation events."""
        return QueryBuilder(self._client, "/aave/events/liquidation")


class UniswapProtocol:
    """Uniswap V3 DEX events with builder pattern."""

    def __init__(self, client: "BaseClient"):
        self._client = client

    def swaps(
        self,
        symbol0: str | None = None,
        symbol1: str | None = None,
        fee: int | None = None,
    ) -> QueryBuilder:
        """
        Start a query for Uniswap V3 swap events.

        Args:
            symbol0: Optional first token symbol (e.g., WETH)
            symbol1: Optional second token symbol (e.g., USDC)
            fee: Optional fee tier (100, 500, 3000, 10000)

        Returns:
            QueryBuilder for chaining filters

        Example:
            query = client.uniswap.swaps("WETH", "USDC", 500).network("ETH").start_block(24000000).end_block(24100000)
            df = query.as_pandas()
        """
        params: dict[str, Any] = {}
        if symbol0:
            params["symbol0"] = symbol0
        if symbol1:
            params["symbol1"] = symbol1
        if fee:
            params["fee"] = fee
        return QueryBuilder(self._client, "/uniswap/events/swap", params)

    def mints(
        self,
        symbol0: str | None = None,
        symbol1: str | None = None,
        fee: int | None = None,
    ) -> QueryBuilder:
        """Start a query for Uniswap V3 mint (add liquidity) events."""
        params: dict[str, Any] = {}
        if symbol0:
            params["symbol0"] = symbol0
        if symbol1:
            params["symbol1"] = symbol1
        if fee:
            params["fee"] = fee
        return QueryBuilder(self._client, "/uniswap/events/mint", params)

    def burns(
        self,
        symbol0: str | None = None,
        symbol1: str | None = None,
        fee: int | None = None,
    ) -> QueryBuilder:
        """Start a query for Uniswap V3 burn (remove liquidity) events."""
        params: dict[str, Any] = {}
        if symbol0:
            params["symbol0"] = symbol0
        if symbol1:
            params["symbol1"] = symbol1
        if fee:
            params["fee"] = fee
        return QueryBuilder(self._client, "/uniswap/events/burn", params)


class LidoProtocol:
    """Lido liquid staking events with builder pattern."""

    def __init__(self, client: "BaseClient"):
        self._client = client

    def deposits(self) -> QueryBuilder:
        """Start a query for Lido stETH deposit events."""
        return QueryBuilder(self._client, "/lido/events/deposit")

    def withdrawals(self) -> QueryBuilder:
        """Start a query for Lido withdrawal events."""
        return QueryBuilder(self._client, "/lido/events/withdraw")


class StaderProtocol:
    """Stader EthX staking events with builder pattern."""

    def __init__(self, client: "BaseClient"):
        self._client = client

    def deposits(self) -> QueryBuilder:
        """Start a query for Stader deposit events."""
        return QueryBuilder(self._client, "/stader/events/deposit")

    def withdrawals(self) -> QueryBuilder:
        """Start a query for Stader withdrawal events."""
        return QueryBuilder(self._client, "/stader/events/withdraw")


class ThresholdProtocol:
    """Threshold tBTC events with builder pattern."""

    def __init__(self, client: "BaseClient"):
        self._client = client

    def mints(self) -> QueryBuilder:
        """Start a query for tBTC mint events."""
        return QueryBuilder(self._client, "/threshold/events/mint")

    def burns(self) -> QueryBuilder:
        """Start a query for tBTC burn/redeem events."""
        return QueryBuilder(self._client, "/threshold/events/burn")


# Async protocol implementations
class AsyncERC20Protocol:
    """Async ERC20 token events with builder pattern."""

    def __init__(self, client: "BaseClient"):
        self._client = client

    def transfers(self, token: str | None = None) -> AsyncQueryBuilder:
        """Start a query for ERC20 transfer events."""
        params = {"token": token} if token else {}
        return AsyncQueryBuilder(self._client, "/erc20/events/transfer", params)

    def approvals(self, token: str | None = None) -> AsyncQueryBuilder:
        """Start a query for ERC20 approval events."""
        params = {"token": token} if token else {}
        return AsyncQueryBuilder(self._client, "/erc20/events/approval", params)


class AsyncNativeTokenProtocol:
    """Async native token events with builder pattern."""

    def __init__(self, client: "BaseClient"):
        self._client = client

    def transfers(self) -> AsyncQueryBuilder:
        """Start a query for native token transfer events."""
        return AsyncQueryBuilder(self._client, "/native_token/events/transfer")


class AsyncAAVEProtocol:
    """Async AAVE V3 events with builder pattern."""

    def __init__(self, client: "BaseClient"):
        self._client = client

    def deposits(self) -> AsyncQueryBuilder:
        """Start a query for AAVE deposit/supply events."""
        return AsyncQueryBuilder(self._client, "/aave/events/deposit")

    def withdrawals(self) -> AsyncQueryBuilder:
        """Start a query for AAVE withdrawal events."""
        return AsyncQueryBuilder(self._client, "/aave/events/withdraw")

    def borrows(self) -> AsyncQueryBuilder:
        """Start a query for AAVE borrow events."""
        return AsyncQueryBuilder(self._client, "/aave/events/borrow")

    def repays(self) -> AsyncQueryBuilder:
        """Start a query for AAVE repay events."""
        return AsyncQueryBuilder(self._client, "/aave/events/repay")

    def liquidations(self) -> AsyncQueryBuilder:
        """Start a query for AAVE liquidation events."""
        return AsyncQueryBuilder(self._client, "/aave/events/liquidation")


class AsyncUniswapProtocol:
    """Async Uniswap V3 events with builder pattern."""

    def __init__(self, client: "BaseClient"):
        self._client = client

    def swaps(
        self,
        symbol0: str | None = None,
        symbol1: str | None = None,
        fee: int | None = None,
    ) -> AsyncQueryBuilder:
        """Start a query for Uniswap V3 swap events."""
        params: dict[str, Any] = {}
        if symbol0:
            params["symbol0"] = symbol0
        if symbol1:
            params["symbol1"] = symbol1
        if fee:
            params["fee"] = fee
        return AsyncQueryBuilder(self._client, "/uniswap/events/swap", params)

    def mints(
        self,
        symbol0: str | None = None,
        symbol1: str | None = None,
        fee: int | None = None,
    ) -> AsyncQueryBuilder:
        """Start a query for Uniswap V3 mint events."""
        params: dict[str, Any] = {}
        if symbol0:
            params["symbol0"] = symbol0
        if symbol1:
            params["symbol1"] = symbol1
        if fee:
            params["fee"] = fee
        return AsyncQueryBuilder(self._client, "/uniswap/events/mint", params)

    def burns(
        self,
        symbol0: str | None = None,
        symbol1: str | None = None,
        fee: int | None = None,
    ) -> AsyncQueryBuilder:
        """Start a query for Uniswap V3 burn events."""
        params: dict[str, Any] = {}
        if symbol0:
            params["symbol0"] = symbol0
        if symbol1:
            params["symbol1"] = symbol1
        if fee:
            params["fee"] = fee
        return AsyncQueryBuilder(self._client, "/uniswap/events/burn", params)


class AsyncLidoProtocol:
    """Async Lido events with builder pattern."""

    def __init__(self, client: "BaseClient"):
        self._client = client

    def deposits(self) -> AsyncQueryBuilder:
        """Start a query for Lido deposit events."""
        return AsyncQueryBuilder(self._client, "/lido/events/deposit")

    def withdrawals(self) -> AsyncQueryBuilder:
        """Start a query for Lido withdrawal events."""
        return AsyncQueryBuilder(self._client, "/lido/events/withdraw")


class AsyncStaderProtocol:
    """Async Stader events with builder pattern."""

    def __init__(self, client: "BaseClient"):
        self._client = client

    def deposits(self) -> AsyncQueryBuilder:
        """Start a query for Stader deposit events."""
        return AsyncQueryBuilder(self._client, "/stader/events/deposit")

    def withdrawals(self) -> AsyncQueryBuilder:
        """Start a query for Stader withdrawal events."""
        return AsyncQueryBuilder(self._client, "/stader/events/withdraw")


class AsyncThresholdProtocol:
    """Async Threshold events with builder pattern."""

    def __init__(self, client: "BaseClient"):
        self._client = client

    def mints(self) -> AsyncQueryBuilder:
        """Start a query for tBTC mint events."""
        return AsyncQueryBuilder(self._client, "/threshold/events/mint")

    def burns(self) -> AsyncQueryBuilder:
        """Start a query for tBTC burn events."""
        return AsyncQueryBuilder(self._client, "/threshold/events/burn")
