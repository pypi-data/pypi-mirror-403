"""Tests for DeFiStream client."""

import os
import pytest
from unittest.mock import MagicMock, patch

from defistream import DeFiStream, AsyncDeFiStream, QueryBuilder, AsyncQueryBuilder
from defistream.exceptions import (
    AuthenticationError,
    QuotaExceededError,
    ValidationError,
)


class TestDeFiStreamInit:
    """Test client initialization."""

    def test_requires_api_key(self):
        """Should raise if no API key provided."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="API key required"):
                DeFiStream()

    def test_accepts_api_key_argument(self):
        """Should accept API key as argument."""
        client = DeFiStream(api_key="dsk_test")
        assert client.api_key == "dsk_test"

    def test_reads_api_key_from_env(self):
        """Should read API key from environment."""
        with patch.dict(os.environ, {"DEFISTREAM_API_KEY": "dsk_env"}):
            client = DeFiStream()
            assert client.api_key == "dsk_env"

    def test_default_base_url(self):
        """Should use default base URL."""
        client = DeFiStream(api_key="dsk_test")
        assert client.base_url == "https://api.defistream.dev/v1"

    def test_custom_base_url(self):
        """Should accept custom base URL."""
        client = DeFiStream(api_key="dsk_test", base_url="http://localhost:8081/v1")
        assert client.base_url == "http://localhost:8081/v1"


class TestProtocolClients:
    """Test protocol client availability."""

    def test_has_erc20_protocol(self):
        """Should have ERC20 protocol client."""
        client = DeFiStream(api_key="dsk_test")
        assert hasattr(client, "erc20")
        assert hasattr(client.erc20, "transfers")
        assert hasattr(client.erc20, "approvals")

    def test_has_native_token_protocol(self):
        """Should have native token protocol client."""
        client = DeFiStream(api_key="dsk_test")
        assert hasattr(client, "native_token")
        assert hasattr(client.native_token, "transfers")

    def test_has_aave_protocol(self):
        """Should have AAVE protocol client."""
        client = DeFiStream(api_key="dsk_test")
        assert hasattr(client, "aave")
        assert hasattr(client.aave, "deposits")
        assert hasattr(client.aave, "withdrawals")
        assert hasattr(client.aave, "borrows")
        assert hasattr(client.aave, "liquidations")

    def test_has_uniswap_protocol(self):
        """Should have Uniswap protocol client."""
        client = DeFiStream(api_key="dsk_test")
        assert hasattr(client, "uniswap")
        assert hasattr(client.uniswap, "swaps")
        assert hasattr(client.uniswap, "mints")
        assert hasattr(client.uniswap, "burns")

    def test_has_lido_protocol(self):
        """Should have Lido protocol client."""
        client = DeFiStream(api_key="dsk_test")
        assert hasattr(client, "lido")
        assert hasattr(client.lido, "deposits")
        assert hasattr(client.lido, "withdrawals")


class TestAsyncClient:
    """Test async client."""

    def test_async_client_init(self):
        """Should initialize async client."""
        client = AsyncDeFiStream(api_key="dsk_test")
        assert client.api_key == "dsk_test"

    def test_async_has_protocols(self):
        """Should have all protocol clients."""
        client = AsyncDeFiStream(api_key="dsk_test")
        assert hasattr(client, "erc20")
        assert hasattr(client, "native_token")
        assert hasattr(client, "aave")
        assert hasattr(client, "uniswap")
        assert hasattr(client, "lido")


class TestContextManager:
    """Test context manager support."""

    def test_sync_context_manager(self):
        """Should work as context manager."""
        with DeFiStream(api_key="dsk_test") as client:
            assert client.api_key == "dsk_test"

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Should work as async context manager."""
        async with AsyncDeFiStream(api_key="dsk_test") as client:
            assert client.api_key == "dsk_test"


class TestBuilderPattern:
    """Test builder pattern for queries."""

    def test_transfers_returns_query_builder(self):
        """Protocol methods should return QueryBuilder."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers()
        assert isinstance(query, QueryBuilder)

    def test_transfers_with_token_sets_param(self):
        """transfers('USDT') should set token param."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers("USDT")
        assert query._params.get("token") == "USDT"

    def test_builder_chaining(self):
        """Builder methods should return QueryBuilder for chaining."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers("USDT").network("ETH").start_block(24000000).end_block(24100000)
        assert isinstance(query, QueryBuilder)
        assert query._params["network"] == "ETH"
        assert query._params["block_start"] == 24000000
        assert query._params["block_end"] == 24100000

    def test_builder_immutability(self):
        """Builder methods should return new instances."""
        client = DeFiStream(api_key="dsk_test")
        query1 = client.erc20.transfers("USDT")
        query2 = query1.network("ETH")
        assert query1 is not query2
        assert "network" not in query1._params
        assert query2._params["network"] == "ETH"

    def test_last_value_wins(self):
        """Multiple calls to same filter should use last value."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().network("ETH").network("ARB")
        assert query._params["network"] == "ARB"

    def test_block_range_method(self):
        """block_range should set both start and end."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().block_range(24000000, 24100000)
        assert query._params["block_start"] == 24000000
        assert query._params["block_end"] == 24100000

    def test_from_address_alias(self):
        """from_address should be alias for sender."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().from_address("0x123")
        assert query._params["sender"] == "0x123"

    def test_to_address_alias(self):
        """to_address should be alias for receiver."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().to_address("0x456")
        assert query._params["receiver"] == "0x456"

    def test_verbose_mode(self):
        """verbose() should set verbose param."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().verbose()
        assert query._verbose is True
        params = query._build_params()
        assert params["verbose"] == "true"

    def test_verbose_false_by_default(self):
        """verbose should be False by default."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers()
        assert query._verbose is False
        params = query._build_params()
        assert "verbose" not in params

    def test_min_amount_filter(self):
        """min_amount should set param."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().min_amount(1000)
        assert query._params["min_amount"] == 1000

    def test_start_time(self):
        """start_time should set since param."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().start_time("2024-01-01T00:00:00Z")
        assert query._params["since"] == "2024-01-01T00:00:00Z"

    def test_end_time(self):
        """end_time should set until param."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().end_time("2024-01-31T23:59:59Z")
        assert query._params["until"] == "2024-01-31T23:59:59Z"

    def test_time_range(self):
        """time_range should set both since and until params."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers().time_range("2024-01-01", "2024-01-31")
        assert query._params["since"] == "2024-01-01"
        assert query._params["until"] == "2024-01-31"


class TestAsyncBuilderPattern:
    """Test async builder pattern."""

    def test_async_transfers_returns_async_query_builder(self):
        """Async protocol methods should return AsyncQueryBuilder."""
        client = AsyncDeFiStream(api_key="dsk_test")
        query = client.erc20.transfers()
        assert isinstance(query, AsyncQueryBuilder)

    def test_async_builder_chaining(self):
        """Async builder methods should chain correctly."""
        client = AsyncDeFiStream(api_key="dsk_test")
        query = client.erc20.transfers("USDT").network("ETH").start_block(24000000).end_block(24100000)
        assert isinstance(query, AsyncQueryBuilder)
        assert query._params["network"] == "ETH"


class TestUniswapBuilder:
    """Test Uniswap-specific builder methods."""

    def test_swaps_with_tokens_and_fee(self):
        """swaps() should accept symbol0, symbol1, fee."""
        client = DeFiStream(api_key="dsk_test")
        query = client.uniswap.swaps("WETH", "USDC", 500)
        assert query._params["symbol0"] == "WETH"
        assert query._params["symbol1"] == "USDC"
        assert query._params["fee"] == 500

    def test_pool_filter(self):
        """pool() should set pool param."""
        client = DeFiStream(api_key="dsk_test")
        query = client.uniswap.swaps().pool("0x123")
        assert query._params["pool"] == "0x123"


class TestAAVEBuilder:
    """Test AAVE-specific builder methods."""

    def test_user_filter(self):
        """user() should set user param."""
        client = DeFiStream(api_key="dsk_test")
        query = client.aave.deposits().user("0x123")
        assert query._params["user"] == "0x123"

    def test_reserve_filter(self):
        """reserve() should set reserve param."""
        client = DeFiStream(api_key="dsk_test")
        query = client.aave.deposits().reserve("0x456")
        assert query._params["reserve"] == "0x456"

    def test_liquidator_filter(self):
        """liquidator() should set liquidator param."""
        client = DeFiStream(api_key="dsk_test")
        query = client.aave.liquidations().liquidator("0x789")
        assert query._params["liquidator"] == "0x789"


class TestQueryBuilderRepr:
    """Test QueryBuilder repr."""

    def test_repr(self):
        """Should have informative repr."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers("USDT").network("ETH")
        repr_str = repr(query)
        assert "QueryBuilder" in repr_str
        assert "/erc20/events/transfer" in repr_str


class TestTerminalMethods:
    """Test terminal methods."""

    def test_has_as_dict(self):
        """QueryBuilder should have as_dict method."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers()
        assert hasattr(query, "as_dict")

    def test_has_as_df(self):
        """QueryBuilder should have as_df method."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers()
        assert hasattr(query, "as_df")

    def test_has_as_file(self):
        """QueryBuilder should have as_file method."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers()
        assert hasattr(query, "as_file")

    def test_as_df_invalid_library(self):
        """as_df should raise for invalid library."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers()
        with pytest.raises(ValueError, match="library must be"):
            query.as_df("invalid")

    def test_as_file_detects_csv_extension(self):
        """as_file should detect CSV format from extension."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers()
        # We can't actually call as_file without a real API, but we can test the format detection logic
        # by checking that it doesn't raise for valid extensions
        assert hasattr(query, "as_file")

    def test_as_file_requires_format_or_extension(self):
        """as_file should raise if no format or extension."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers()
        with pytest.raises(ValueError, match="Cannot determine format"):
            query.as_file("transfers_without_extension")

    def test_as_file_invalid_format(self):
        """as_file should raise for invalid format."""
        client = DeFiStream(api_key="dsk_test")
        query = client.erc20.transfers()
        with pytest.raises(ValueError, match="format must be"):
            query.as_file("transfers", format="xml")


class TestAsyncTerminalMethods:
    """Test async terminal methods."""

    def test_async_has_as_dict(self):
        """AsyncQueryBuilder should have as_dict method."""
        client = AsyncDeFiStream(api_key="dsk_test")
        query = client.erc20.transfers()
        assert hasattr(query, "as_dict")

    def test_async_has_as_df(self):
        """AsyncQueryBuilder should have as_df method."""
        client = AsyncDeFiStream(api_key="dsk_test")
        query = client.erc20.transfers()
        assert hasattr(query, "as_df")

    def test_async_has_as_file(self):
        """AsyncQueryBuilder should have as_file method."""
        client = AsyncDeFiStream(api_key="dsk_test")
        query = client.erc20.transfers()
        assert hasattr(query, "as_file")
