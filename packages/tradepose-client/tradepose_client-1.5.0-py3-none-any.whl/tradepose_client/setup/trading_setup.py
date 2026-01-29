"""TradingSetup - Synchronous wrapper for trading configuration.

Provides a sync API for:
- Querying strategies, instruments, accounts, portfolios, bindings, slots
- Creating portfolios and accounts
- Binding portfolios to accounts and accounts to slots

Uses threading + asyncio pattern (same as BatchTester) to wrap async operations.
"""

from __future__ import annotations

import asyncio
import logging
import threading
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tradepose_models.strategy import StrategyConfig

logger = logging.getLogger(__name__)


# =============================================================================
# INFO CLASSES (Simplified response models for sync API)
# =============================================================================


@dataclass
class BlueprintInfo:
    """Blueprint identifier with id and name."""

    id: str
    name: str


@dataclass
class StrategyInfo:
    """Strategy information."""

    id: str
    name: str
    base_instrument: str
    base_freq: str
    note: str
    base_blueprint: BlueprintInfo
    advanced_blueprints: list[BlueprintInfo]


@dataclass
class InstrumentInfo:
    """Instrument information."""

    id: int
    symbol: str
    account_source: str
    broker_type: str
    market_type: str
    base_currency: str
    quote_currency: str
    tick_size: str
    lot_size: str
    price_precision: int
    quantity_precision: int
    point_value: str
    status: str


@dataclass
class AccountInfo:
    """Account information."""

    id: str
    name: str
    broker_type: str
    available_markets: list[str]
    status: str
    is_archived: bool
    account_source: str | None = None


@dataclass
class PortfolioInfo:
    """Portfolio information."""

    name: str
    capital: str
    currency: str
    account_source: str


@dataclass
class BindingInfo:
    """Binding information."""

    id: str
    account_id: str
    portfolio_id: str
    execution_mode: str
    is_active: bool


@dataclass
class SlotInfo:
    """Slot information."""

    id: str
    node_seq: int
    slot_idx: int
    account_id: str | None
    bound_at: datetime | None


# =============================================================================
# TRADING SETUP CLASS
# =============================================================================


class TradingSetup:
    """Synchronous trading configuration utility.

    Wraps async operations using threading + asyncio pattern.
    Users don't need to write async/await.

    Example:
        >>> from tradepose_client import TradingSetup
        >>>
        >>> setup = TradingSetup(api_key="tp_live_xxx")
        >>>
        >>> # Query existing resources (sync)
        >>> strategies = setup.list_strategies()
        >>> instruments = setup.list_instruments(symbol="BTC")
        >>> accounts = setup.list_accounts()
        >>> slots = setup.list_slots()
        >>>
        >>> # Create resources (sync)
        >>> portfolio = setup.create_portfolio(...)
        >>> account = setup.create_account(...)
        >>>
        >>> # Bind resources (sync)
        >>> binding = setup.bind_portfolio(account_id, portfolio_id)
        >>> slot = setup.bind_slot(node_seq=0, slot_idx=0, account_id=account_id)
    """

    def __init__(
        self,
        api_key: str,
        server_url: str = "https://api.tradepose.com",
    ):
        """Initialize TradingSetup.

        Args:
            api_key: API key for authentication
            server_url: Gateway server URL
        """
        self._api_key = api_key
        self._server_url = server_url

    # =========================================================================
    # QUERY METHODS (sync, I/O)
    # =========================================================================

    def list_strategies(self, *, include_archived: bool = True) -> list[StrategyInfo]:
        """List all strategies for the authenticated user.

        Args:
            include_archived: Whether to include archived strategies. Defaults to True.

        Returns:
            List of StrategyInfo objects
        """
        return self._run_async(self._async_list_strategies(include_archived=include_archived))

    def get_strategy(self, strategy_id: str) -> StrategyConfig:
        """Get complete strategy configuration by ID.

        Args:
            strategy_id: Strategy UUID (from StrategyInfo.id)

        Returns:
            StrategyConfig with full strategy details including blueprints
        """
        return self._run_async(self._async_get_strategy(strategy_id))

    def list_instruments(
        self,
        *,
        symbol: str | None = None,
        account_source: str | None = None,
        broker_type: str | None = None,
        market_type: str | None = None,
        limit: int = 100,
    ) -> list[InstrumentInfo]:
        """List available instruments.

        Args:
            symbol: Filter by symbol (partial match)
            account_source: Filter by account source (e.g., 'BINANCE')
            broker_type: Filter by broker type
            market_type: Filter by market type (e.g., 'spot', 'futures')
            limit: Maximum results (default: 100)

        Returns:
            List of InstrumentInfo objects
        """
        return self._run_async(
            self._async_list_instruments(
                symbol=symbol,
                account_source=account_source,
                broker_type=broker_type,
                market_type=market_type,
                limit=limit,
            )
        )

    def list_accounts(self) -> list[AccountInfo]:
        """List all accounts for the authenticated user.

        Returns:
            List of AccountInfo objects
        """
        return self._run_async(self._async_list_accounts())

    def list_portfolios(self) -> list[PortfolioInfo]:
        """List all portfolios for the authenticated user.

        Returns:
            List of PortfolioInfo objects
        """
        return self._run_async(self._async_list_portfolios())

    def list_bindings(self) -> list[BindingInfo]:
        """List all bindings for the authenticated user.

        Returns:
            List of BindingInfo objects
        """
        return self._run_async(self._async_list_bindings())

    def list_slots(self) -> list[SlotInfo]:
        """List all trader slots for the authenticated user.

        Returns:
            List of SlotInfo objects
        """
        return self._run_async(self._async_list_slots())

    # =========================================================================
    # CREATE METHODS (sync, I/O)
    # =========================================================================

    def create_portfolio(
        self,
        name: str,
        capital: Decimal | int | float,
        currency: str,
        account_source: str,
        selections: list[dict],
        *,
        instrument_mapping: dict[str, int] | None = None,
    ) -> PortfolioInfo:
        """Create a new portfolio.

        Args:
            name: Portfolio name (unique per user)
            capital: Portfolio capital
            currency: Currency code (e.g., 'USDT', 'USD')
            account_source: Account source (e.g., 'BINANCE', 'FTMO')
            selections: List of strategy selections
                [{"strategy_name": "...", "blueprint_name": "..."}]
            instrument_mapping: Optional instrument mapping
                {"signal_instrument": trading_instrument_id}

        Returns:
            Created PortfolioInfo
        """
        return self._run_async(
            self._async_create_portfolio(
                name=name,
                capital=capital,
                currency=currency,
                account_source=account_source,
                selections=selections,
                instrument_mapping=instrument_mapping,
            )
        )

    def create_account(
        self,
        name: str,
        broker_type: str,
        credentials: dict,
        *,
        available_markets: list[str] | None = None,
        account_source: str | None = None,
    ) -> AccountInfo:
        """Create a new broker account.

        Args:
            name: Account name (unique per user)
            broker_type: Broker type (e.g., 'binance', 'mt5')
            credentials: Broker credentials (will be encrypted)
            available_markets: Available market types (default: ['spot'])
            account_source: Account source (e.g., 'FTMO', 'FIVEPERCENT').
                Required for MT5 accounts.

        Returns:
            Created AccountInfo
        """
        return self._run_async(
            self._async_create_account(
                name=name,
                broker_type=broker_type,
                credentials=credentials,
                available_markets=available_markets,
                account_source=account_source,
            )
        )

    # =========================================================================
    # BIND METHODS (sync, I/O)
    # =========================================================================

    def bind_portfolio(
        self,
        account_id: str,
        portfolio_name: str,
        *,
        execution_mode: str = "signal_priority",
    ) -> BindingInfo:
        """Bind a portfolio to an account.

        Args:
            account_id: Account UUID
            portfolio_name: Portfolio name
            execution_mode: Execution mode (default: 'signal_priority')

        Returns:
            Created BindingInfo
        """
        return self._run_async(
            self._async_bind_portfolio(
                account_id=account_id,
                portfolio_name=portfolio_name,
                execution_mode=execution_mode,
            )
        )

    def bind_slot(
        self,
        node_seq: int,
        slot_idx: int,
        account_id: str,
    ) -> SlotInfo:
        """Bind an account to a trader slot.

        Args:
            node_seq: Node sequence number (0-based)
            slot_idx: Slot index within the node (0-based)
            account_id: Account UUID to bind

        Returns:
            Updated SlotInfo
        """
        return self._run_async(
            self._async_bind_slot(
                node_seq=node_seq,
                slot_idx=slot_idx,
                account_id=account_id,
            )
        )

    def unbind_slot(
        self,
        node_seq: int,
        slot_idx: int,
    ) -> SlotInfo:
        """Unbind an account from a trader slot.

        Args:
            node_seq: Node sequence number (0-based)
            slot_idx: Slot index within the node (0-based)

        Returns:
            Updated SlotInfo (account_id will be None)
        """
        return self._run_async(
            self._async_unbind_slot(
                node_seq=node_seq,
                slot_idx=slot_idx,
            )
        )

    # =========================================================================
    # INTERNAL: ASYNC IMPLEMENTATIONS
    # =========================================================================

    async def _async_list_strategies(self, *, include_archived: bool = True) -> list[StrategyInfo]:
        """Async implementation of list_strategies."""
        from tradepose_client import TradePoseClient

        async with TradePoseClient(api_key=self._api_key, server_url=self._server_url) as client:
            response = await client.strategies.list(archived=include_archived)
            return [
                StrategyInfo(
                    id=s.id,
                    name=s.name,
                    base_instrument=s.base_instrument,
                    base_freq=s.base_freq,
                    note=s.note,
                    base_blueprint=BlueprintInfo(
                        id=s.base_blueprint.id,
                        name=s.base_blueprint.name,
                    ),
                    advanced_blueprints=[
                        BlueprintInfo(id=bp.id, name=bp.name) for bp in s.advanced_blueprints
                    ],
                )
                for s in response.strategies
            ]

    async def _async_get_strategy(self, strategy_id: str) -> StrategyConfig:
        """Async implementation of get_strategy."""
        from tradepose_client import TradePoseClient

        async with TradePoseClient(api_key=self._api_key, server_url=self._server_url) as client:
            return await client.strategies.get(strategy_id)

    async def _async_list_instruments(
        self,
        *,
        symbol: str | None = None,
        account_source: str | None = None,
        broker_type: str | None = None,
        market_type: str | None = None,
        limit: int = 100,
    ) -> list[InstrumentInfo]:
        """Async implementation of list_instruments."""
        from tradepose_client import TradePoseClient

        async with TradePoseClient(api_key=self._api_key, server_url=self._server_url) as client:
            response = await client.instruments.list(
                symbol=symbol,
                account_source=account_source,
                broker_type=broker_type,
                market_type=market_type,
                limit=limit,
            )
            return [
                InstrumentInfo(
                    id=i.id,
                    symbol=i.symbol,
                    account_source=i.account_source,
                    broker_type=i.broker_type,
                    market_type=i.market_type,
                    base_currency=i.base_currency,
                    quote_currency=i.quote_currency,
                    tick_size=i.tick_size,
                    lot_size=i.lot_size,
                    price_precision=i.price_precision,
                    quantity_precision=i.quantity_precision,
                    point_value=i.point_value,
                    status=i.status,
                )
                for i in response.instruments
            ]

    async def _async_list_accounts(self) -> list[AccountInfo]:
        """Async implementation of list_accounts."""
        from tradepose_client import TradePoseClient

        async with TradePoseClient(api_key=self._api_key, server_url=self._server_url) as client:
            response = await client.accounts.list()
            return [
                AccountInfo(
                    id=a.id,
                    name=a.name,
                    broker_type=a.broker_type.value
                    if hasattr(a.broker_type, "value")
                    else str(a.broker_type),
                    available_markets=[
                        m.value if hasattr(m, "value") else str(m) for m in a.available_markets
                    ],
                    status=a.status.value if hasattr(a.status, "value") else str(a.status),
                    is_archived=a.is_archived,
                    account_source=a.account_source.value
                    if a.account_source and hasattr(a.account_source, "value")
                    else (str(a.account_source) if a.account_source else None),
                )
                for a in response.accounts
            ]

    async def _async_list_portfolios(self) -> list[PortfolioInfo]:
        """Async implementation of list_portfolios."""
        from tradepose_client import TradePoseClient

        async with TradePoseClient(api_key=self._api_key, server_url=self._server_url) as client:
            response = await client.portfolios.list()
            return [
                PortfolioInfo(
                    name=p.name,
                    capital=str(p.capital),
                    currency=p.currency,
                    account_source=p.account_source,
                )
                for p in response.portfolios
            ]

    async def _async_list_bindings(self) -> list[BindingInfo]:
        """Async implementation of list_bindings."""
        from tradepose_client import TradePoseClient

        async with TradePoseClient(api_key=self._api_key, server_url=self._server_url) as client:
            response = await client.bindings.list()
            return [
                BindingInfo(
                    id=str(b.id),
                    account_id=str(b.account_id),
                    portfolio_id=str(b.portfolio_id),
                    execution_mode=b.execution_mode,
                    is_active=b.is_active,
                )
                for b in response.bindings
            ]

    async def _async_list_slots(self) -> list[SlotInfo]:
        """Async implementation of list_slots."""
        from tradepose_client import TradePoseClient

        async with TradePoseClient(api_key=self._api_key, server_url=self._server_url) as client:
            response = await client.slots.list()
            return [
                SlotInfo(
                    id=s.id,
                    node_seq=s.node_seq,
                    slot_idx=s.slot_idx,
                    account_id=s.account_id,
                    bound_at=s.bound_at,
                )
                for s in response.slots
            ]

    async def _async_create_portfolio(
        self,
        name: str,
        capital: Decimal | int | float,
        currency: str,
        account_source: str,
        selections: list[dict],
        instrument_mapping: dict[str, int] | None = None,
    ) -> PortfolioInfo:
        """Async implementation of create_portfolio."""
        from tradepose_client import TradePoseClient
        from tradepose_client.resources.portfolios import PortfolioCreateRequest

        async with TradePoseClient(api_key=self._api_key, server_url=self._server_url) as client:
            request = PortfolioCreateRequest(
                name=name,
                capital=str(capital),
                currency=currency,
                account_source=account_source,
                selections=selections,
            )
            response = await client.portfolios.create(request)
            return PortfolioInfo(
                name=response.name,
                capital=str(response.capital),
                currency=response.currency,
                account_source=response.account_source,
            )

    async def _async_create_account(
        self,
        name: str,
        broker_type: str,
        credentials: dict,
        available_markets: list[str] | None = None,
        account_source: str | None = None,
    ) -> AccountInfo:
        """Async implementation of create_account."""
        from tradepose_models.broker import BrokerType, MarketType
        from tradepose_models.enums import AccountSource

        from tradepose_client import TradePoseClient
        from tradepose_client.resources.accounts import AccountCreateRequest

        async with TradePoseClient(api_key=self._api_key, server_url=self._server_url) as client:
            markets = (
                [MarketType.SPOT]
                if not available_markets
                else [MarketType(m) for m in available_markets]
            )
            request = AccountCreateRequest(
                name=name,
                broker_type=BrokerType(broker_type),
                credentials=credentials,
                available_markets=markets,
                account_source=AccountSource(account_source) if account_source else None,
            )
            response = await client.accounts.create(request)
            return AccountInfo(
                id=response.id,
                name=response.name,
                broker_type=response.broker_type.value
                if hasattr(response.broker_type, "value")
                else str(response.broker_type),
                available_markets=[
                    m.value if hasattr(m, "value") else str(m) for m in response.available_markets
                ],
                status=response.status.value
                if hasattr(response.status, "value")
                else str(response.status),
                is_archived=response.is_archived,
                account_source=response.account_source.value
                if response.account_source and hasattr(response.account_source, "value")
                else (str(response.account_source) if response.account_source else None),
            )

    async def _async_bind_portfolio(
        self,
        account_id: str,
        portfolio_name: str,
        execution_mode: str = "signal_priority",
    ) -> BindingInfo:
        """Async implementation of bind_portfolio."""
        from tradepose_client import TradePoseClient
        from tradepose_client.resources.bindings import BindingCreateRequest

        async with TradePoseClient(api_key=self._api_key, server_url=self._server_url) as client:
            request = BindingCreateRequest(
                account_id=account_id,
                portfolio_name=portfolio_name,
                execution_mode=execution_mode,
            )
            response = await client.bindings.create(request)
            return BindingInfo(
                id=str(response.id),
                account_id=str(response.account_id),
                portfolio_id=str(response.portfolio_id),
                execution_mode=response.execution_mode,
                is_active=response.is_active,
            )

    async def _async_bind_slot(
        self,
        node_seq: int,
        slot_idx: int,
        account_id: str,
    ) -> SlotInfo:
        """Async implementation of bind_slot."""
        from tradepose_client import TradePoseClient

        async with TradePoseClient(api_key=self._api_key, server_url=self._server_url) as client:
            response = await client.slots.bind(node_seq, slot_idx, account_id)
            return SlotInfo(
                id=response.id,
                node_seq=response.node_seq,
                slot_idx=response.slot_idx,
                account_id=response.account_id,
                bound_at=response.bound_at,
            )

    async def _async_unbind_slot(
        self,
        node_seq: int,
        slot_idx: int,
    ) -> SlotInfo:
        """Async implementation of unbind_slot."""
        from tradepose_client import TradePoseClient

        async with TradePoseClient(api_key=self._api_key, server_url=self._server_url) as client:
            response = await client.slots.unbind(node_seq, slot_idx)
            return SlotInfo(
                id=response.id,
                node_seq=response.node_seq,
                slot_idx=response.slot_idx,
                account_id=response.account_id,
                bound_at=response.bound_at,
            )

    # =========================================================================
    # INTERNAL: ASYNC RUNNER (from BatchTester pattern)
    # =========================================================================

    def _run_async(self, coro) -> Any:
        """Run async coroutine in a separate thread.

        Uses threading to avoid blocking the main thread and to handle
        cases where an event loop is already running (e.g., Jupyter).

        Args:
            coro: Coroutine to execute

        Returns:
            Result from the coroutine
        """
        result_container = []
        exception_container = []

        def _run_in_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(coro)
                result_container.append(result)
            except Exception as e:
                exception_container.append(e)
            finally:
                loop.close()

        thread = threading.Thread(target=_run_in_thread)
        thread.start()
        thread.join()

        if exception_container:
            raise exception_container[0]

        return result_container[0] if result_container else None
