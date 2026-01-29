"""Query builder for DeFiStream API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .client import BaseClient


class QueryBuilder:
    """
    Builder for constructing and executing DeFiStream API queries.

    Query is only executed when a terminal method is called:
    - as_dict() - returns list of dictionaries
    - as_df() - returns pandas DataFrame (default) or polars DataFrame
    - as_file() - saves to CSV, Parquet, or JSON file

    Example:
        query = client.erc20.transfers("USDT").network("ETH").block_range(21000000, 21010000)
        query = query.min_amount(1000).sender("0x...")
        df = query.as_df()  # pandas DataFrame
        df = query.as_df("polars")  # polars DataFrame
        query.as_file("transfers.csv")  # save to CSV
    """

    def __init__(
        self,
        client: "BaseClient",
        endpoint: str,
        initial_params: dict[str, Any] | None = None,
    ):
        self._client = client
        self._endpoint = endpoint
        self._params: dict[str, Any] = initial_params or {}
        self._verbose = False

    def _copy_with(self, **updates: Any) -> "QueryBuilder":
        """Create a copy with updated parameters."""
        new_builder = QueryBuilder(self._client, self._endpoint, self._params.copy())
        new_builder._verbose = self._verbose
        for key, value in updates.items():
            if key == "verbose":
                new_builder._verbose = value
            elif value is not None:
                new_builder._params[key] = value
        return new_builder

    # Network and block range
    def network(self, network: str) -> "QueryBuilder":
        """Set the network (ETH, ARB, BASE, OP, POLYGON, etc.)."""
        return self._copy_with(network=network)

    def start_block(self, block: int) -> "QueryBuilder":
        """Set the starting block number."""
        return self._copy_with(block_start=block)

    def end_block(self, block: int) -> "QueryBuilder":
        """Set the ending block number."""
        return self._copy_with(block_end=block)

    def block_range(self, start: int, end: int) -> "QueryBuilder":
        """Set both start and end block numbers."""
        return self._copy_with(block_start=start, block_end=end)

    # Time range
    def start_time(self, timestamp: str) -> "QueryBuilder":
        """Set the starting time (ISO format or Unix timestamp)."""
        return self._copy_with(since=timestamp)

    def end_time(self, timestamp: str) -> "QueryBuilder":
        """Set the ending time (ISO format or Unix timestamp)."""
        return self._copy_with(until=timestamp)

    def time_range(self, start: str, end: str) -> "QueryBuilder":
        """Set both start and end times."""
        return self._copy_with(since=start, until=end)

    # ERC20 and Native Token filters
    def sender(self, address: str) -> "QueryBuilder":
        """Filter by sender address (ERC20, Native Token)."""
        return self._copy_with(sender=address)

    def receiver(self, address: str) -> "QueryBuilder":
        """Filter by receiver address (ERC20, Native Token)."""
        return self._copy_with(receiver=address)

    def from_address(self, address: str) -> "QueryBuilder":
        """Filter by sender address (alias for sender)."""
        return self.sender(address)

    def to_address(self, address: str) -> "QueryBuilder":
        """Filter by receiver address (alias for receiver)."""
        return self.receiver(address)

    def min_amount(self, amount: float) -> "QueryBuilder":
        """Filter by minimum amount (ERC20, Native Token)."""
        return self._copy_with(min_amount=amount)

    def max_amount(self, amount: float) -> "QueryBuilder":
        """Filter by maximum amount (ERC20, Native Token)."""
        return self._copy_with(max_amount=amount)

    # ERC20 specific
    def token(self, symbol: str) -> "QueryBuilder":
        """Set token symbol or address (ERC20)."""
        return self._copy_with(token=symbol)

    # AAVE specific
    def eth_market_type(self, market_type: str) -> "QueryBuilder":
        """Set AAVE market type for ETH network: 'Core', 'Prime', or 'EtherFi'. Default: 'Core'."""
        return self._copy_with(eth_market_type=market_type)

    # Uniswap specific
    def symbol0(self, symbol: str) -> "QueryBuilder":
        """Set first token symbol (Uniswap)."""
        return self._copy_with(symbol0=symbol)

    def symbol1(self, symbol: str) -> "QueryBuilder":
        """Set second token symbol (Uniswap)."""
        return self._copy_with(symbol1=symbol)

    def fee(self, fee_tier: int) -> "QueryBuilder":
        """Set fee tier (Uniswap): 100, 500, 3000, 10000."""
        return self._copy_with(fee=fee_tier)

    # Verbose mode
    def verbose(self, enabled: bool = True) -> "QueryBuilder":
        """Include all metadata fields (tx_hash, tx_id, log_index, network, name)."""
        return self._copy_with(verbose=enabled)

    # Build final params
    def _build_params(self) -> dict[str, Any]:
        """Build the final query parameters."""
        params = self._params.copy()
        if self._verbose:
            params["verbose"] = "true"
        return params

    # Terminal methods - execute the query
    def as_dict(self) -> list[dict[str, Any]]:
        """
        Execute query and return results as list of dictionaries.

        Uses JSON format from API. Limited to 10,000 blocks.

        Returns:
            List of event dictionaries
        """
        params = self._build_params()
        return self._client._request("GET", self._endpoint, params=params)

    def as_df(self, library: str = "pandas") -> Any:
        """
        Execute query and return results as DataFrame.

        Args:
            library: DataFrame library to use - "pandas" (default) or "polars"

        Returns:
            pandas.DataFrame or polars.DataFrame

        Example:
            df = query.as_df()  # pandas DataFrame
            df = query.as_df("polars")  # polars DataFrame
        """
        if library not in ("pandas", "polars"):
            raise ValueError(f"library must be 'pandas' or 'polars', got '{library}'")
        params = self._build_params()
        params["format"] = "parquet"
        return self._client._request(
            "GET", self._endpoint, params=params, as_dataframe=library
        )

    def as_file(self, path: str, format: str | None = None) -> None:
        """
        Execute query and save results to file.

        Format is automatically determined by file extension, or can be
        explicitly specified.

        Args:
            path: File path to save to
            format: File format - "csv", "parquet", or "json".
                   If None, determined from file extension.

        Example:
            query.as_file("transfers.csv")  # CSV format
            query.as_file("transfers.parquet")  # Parquet format
            query.as_file("transfers.json")  # JSON format
            query.as_file("transfers", format="csv")  # Explicit format
        """
        # Determine format from extension or explicit parameter
        if format is None:
            if path.endswith(".csv"):
                format = "csv"
            elif path.endswith(".parquet"):
                format = "parquet"
            elif path.endswith(".json"):
                format = "json"
            else:
                raise ValueError(
                    f"Cannot determine format from path '{path}'. "
                    "Use a file extension (.csv, .parquet, .json) or specify format explicitly."
                )

        if format not in ("csv", "parquet", "json"):
            raise ValueError(f"format must be 'csv', 'parquet', or 'json', got '{format}'")

        params = self._build_params()

        if format == "json":
            # For JSON, fetch as dict and write manually
            import json
            results = self.as_dict()
            with open(path, "w") as f:
                json.dump(results, f, indent=2)
        else:
            # For CSV and Parquet, use API format parameter
            params["format"] = format
            self._client._request("GET", self._endpoint, params=params, output_file=path)

    def __repr__(self) -> str:
        return f"QueryBuilder(endpoint={self._endpoint!r}, params={self._params!r}, verbose={self._verbose})"


class AsyncQueryBuilder:
    """
    Async builder for constructing and executing DeFiStream API queries.

    Query is only executed when a terminal method is called:
    - as_dict() - returns list of dictionaries
    - as_df() - returns pandas DataFrame (default) or polars DataFrame
    - as_file() - saves to CSV, Parquet, or JSON file

    Example:
        query = client.erc20.transfers("USDT").network("ETH").block_range(21000000, 21010000)
        df = await query.as_df()  # pandas DataFrame
        df = await query.as_df("polars")  # polars DataFrame
        await query.as_file("transfers.csv")  # save to CSV
    """

    def __init__(
        self,
        client: "BaseClient",
        endpoint: str,
        initial_params: dict[str, Any] | None = None,
    ):
        self._client = client
        self._endpoint = endpoint
        self._params: dict[str, Any] = initial_params or {}
        self._verbose = False

    def _copy_with(self, **updates: Any) -> "AsyncQueryBuilder":
        """Create a copy with updated parameters."""
        new_builder = AsyncQueryBuilder(self._client, self._endpoint, self._params.copy())
        new_builder._verbose = self._verbose
        for key, value in updates.items():
            if key == "verbose":
                new_builder._verbose = value
            elif value is not None:
                new_builder._params[key] = value
        return new_builder

    # Network and block range
    def network(self, network: str) -> "AsyncQueryBuilder":
        """Set the network (ETH, ARB, BASE, OP, POLYGON, etc.)."""
        return self._copy_with(network=network)

    def start_block(self, block: int) -> "AsyncQueryBuilder":
        """Set the starting block number."""
        return self._copy_with(block_start=block)

    def end_block(self, block: int) -> "AsyncQueryBuilder":
        """Set the ending block number."""
        return self._copy_with(block_end=block)

    def block_range(self, start: int, end: int) -> "AsyncQueryBuilder":
        """Set both start and end block numbers."""
        return self._copy_with(block_start=start, block_end=end)

    # Time range
    def start_time(self, timestamp: str) -> "AsyncQueryBuilder":
        """Set the starting time (ISO format or Unix timestamp)."""
        return self._copy_with(since=timestamp)

    def end_time(self, timestamp: str) -> "AsyncQueryBuilder":
        """Set the ending time (ISO format or Unix timestamp)."""
        return self._copy_with(until=timestamp)

    def time_range(self, start: str, end: str) -> "AsyncQueryBuilder":
        """Set both start and end times."""
        return self._copy_with(since=start, until=end)

    # ERC20 and Native Token filters
    def sender(self, address: str) -> "AsyncQueryBuilder":
        """Filter by sender address (ERC20, Native Token)."""
        return self._copy_with(sender=address)

    def receiver(self, address: str) -> "AsyncQueryBuilder":
        """Filter by receiver address (ERC20, Native Token)."""
        return self._copy_with(receiver=address)

    def from_address(self, address: str) -> "AsyncQueryBuilder":
        """Filter by sender address (alias for sender)."""
        return self.sender(address)

    def to_address(self, address: str) -> "AsyncQueryBuilder":
        """Filter by receiver address (alias for receiver)."""
        return self.receiver(address)

    def min_amount(self, amount: float) -> "AsyncQueryBuilder":
        """Filter by minimum amount (ERC20, Native Token)."""
        return self._copy_with(min_amount=amount)

    def max_amount(self, amount: float) -> "AsyncQueryBuilder":
        """Filter by maximum amount (ERC20, Native Token)."""
        return self._copy_with(max_amount=amount)

    # ERC20 specific
    def token(self, symbol: str) -> "AsyncQueryBuilder":
        """Set token symbol or address (ERC20)."""
        return self._copy_with(token=symbol)

    # AAVE specific
    def eth_market_type(self, market_type: str) -> "AsyncQueryBuilder":
        """Set AAVE market type for ETH network: 'Core', 'Prime', or 'EtherFi'. Default: 'Core'."""
        return self._copy_with(eth_market_type=market_type)

    # Uniswap specific
    def symbol0(self, symbol: str) -> "AsyncQueryBuilder":
        """Set first token symbol (Uniswap)."""
        return self._copy_with(symbol0=symbol)

    def symbol1(self, symbol: str) -> "AsyncQueryBuilder":
        """Set second token symbol (Uniswap)."""
        return self._copy_with(symbol1=symbol)

    def fee(self, fee_tier: int) -> "AsyncQueryBuilder":
        """Set fee tier (Uniswap): 100, 500, 3000, 10000."""
        return self._copy_with(fee=fee_tier)

    # Verbose mode
    def verbose(self, enabled: bool = True) -> "AsyncQueryBuilder":
        """Include all metadata fields (tx_hash, tx_id, log_index, network, name)."""
        return self._copy_with(verbose=enabled)

    # Build final params
    def _build_params(self) -> dict[str, Any]:
        """Build the final query parameters."""
        params = self._params.copy()
        if self._verbose:
            params["verbose"] = "true"
        return params

    # Terminal methods - execute the query (async)
    async def as_dict(self) -> list[dict[str, Any]]:
        """
        Execute query and return results as list of dictionaries.

        Uses JSON format from API. Limited to 10,000 blocks.

        Returns:
            List of event dictionaries
        """
        params = self._build_params()
        return await self._client._request("GET", self._endpoint, params=params)

    async def as_df(self, library: str = "pandas") -> Any:
        """
        Execute query and return results as DataFrame.

        Args:
            library: DataFrame library to use - "pandas" (default) or "polars"

        Returns:
            pandas.DataFrame or polars.DataFrame

        Example:
            df = await query.as_df()  # pandas DataFrame
            df = await query.as_df("polars")  # polars DataFrame
        """
        if library not in ("pandas", "polars"):
            raise ValueError(f"library must be 'pandas' or 'polars', got '{library}'")
        params = self._build_params()
        params["format"] = "parquet"
        return await self._client._request(
            "GET", self._endpoint, params=params, as_dataframe=library
        )

    async def as_file(self, path: str, format: str | None = None) -> None:
        """
        Execute query and save results to file.

        Format is automatically determined by file extension, or can be
        explicitly specified.

        Args:
            path: File path to save to
            format: File format - "csv", "parquet", or "json".
                   If None, determined from file extension.

        Example:
            await query.as_file("transfers.csv")  # CSV format
            await query.as_file("transfers.parquet")  # Parquet format
            await query.as_file("transfers.json")  # JSON format
            await query.as_file("transfers", format="csv")  # Explicit format
        """
        # Determine format from extension or explicit parameter
        if format is None:
            if path.endswith(".csv"):
                format = "csv"
            elif path.endswith(".parquet"):
                format = "parquet"
            elif path.endswith(".json"):
                format = "json"
            else:
                raise ValueError(
                    f"Cannot determine format from path '{path}'. "
                    "Use a file extension (.csv, .parquet, .json) or specify format explicitly."
                )

        if format not in ("csv", "parquet", "json"):
            raise ValueError(f"format must be 'csv', 'parquet', or 'json', got '{format}'")

        params = self._build_params()

        if format == "json":
            # For JSON, fetch as dict and write manually
            import json
            results = await self.as_dict()
            with open(path, "w") as f:
                json.dump(results, f, indent=2)
        else:
            # For CSV and Parquet, use API format parameter
            params["format"] = format
            await self._client._request("GET", self._endpoint, params=params, output_file=path)

    def __repr__(self) -> str:
        return f"AsyncQueryBuilder(endpoint={self._endpoint!r}, params={self._params!r}, verbose={self._verbose})"
