"""Instruments resource for TradePose Client.

This module provides read-only operations for listing available instruments.
"""

import logging
from datetime import datetime

from pydantic import BaseModel

from .base import BaseResource

logger = logging.getLogger(__name__)


# =============================================================================
# RESPONSE MODELS
# =============================================================================


class InstrumentResponse(BaseModel):
    """Instrument response model."""

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
    contract_size: str
    point_value: str
    status: str
    created_at: datetime
    updated_at: datetime


class InstrumentListResponse(BaseModel):
    """Instrument list response model."""

    instruments: list[InstrumentResponse]
    count: int
    total: int
    limit: int
    offset: int


# =============================================================================
# RESOURCE CLASS
# =============================================================================


class InstrumentsResource(BaseResource):
    """Instruments resource (read-only).

    Provides operations for listing available trading instruments.

    Example:
        >>> async with TradePoseClient(api_key="tp_live_xxx") as client:
        ...     # List all instruments
        ...     instruments = await client.instruments.list()
        ...     print(f"Found {instruments.total} instruments")
        ...
        ...     # Filter by symbol
        ...     btc_instruments = await client.instruments.list(symbol="BTC")
        ...
        ...     # Filter by source
        ...     binance = await client.instruments.list(account_source="BINANCE")
    """

    async def list(
        self,
        *,
        symbol: str | None = None,
        account_source: str | None = None,
        broker_type: str | None = None,
        market_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> InstrumentListResponse:
        """List available instruments.

        Args:
            symbol: Filter by symbol (partial match)
            account_source: Filter by account source (e.g., 'BINANCE')
            broker_type: Filter by broker type
            market_type: Filter by market type (e.g., 'spot', 'futures')
            limit: Maximum results (default: 100)
            offset: Results to skip (default: 0)

        Returns:
            List of instruments with pagination info

        Raises:
            TradePoseAPIError: For API errors

        Example:
            >>> instruments = await client.instruments.list(symbol="BTC")
            >>> print(f"Found {instruments.count} BTC instruments")
        """
        logger.debug(f"Listing instruments (symbol={symbol}, limit={limit})")

        params = {"limit": limit, "offset": offset}
        if symbol:
            params["symbol"] = symbol
        if account_source:
            params["account_source"] = account_source
        if broker_type:
            params["broker_type"] = broker_type
        if market_type:
            params["market_type"] = market_type

        response = await self._get("/api/v1/instruments", params=params)

        result = InstrumentListResponse(**response)
        logger.info(f"Listed {result.count} instruments (total: {result.total})")
        return result

    async def get(self, instrument_id: int) -> InstrumentResponse:
        """Get a single instrument by ID.

        Args:
            instrument_id: Instrument ID

        Returns:
            Instrument details

        Raises:
            ResourceNotFoundError: If instrument not found
            TradePoseAPIError: For other API errors

        Example:
            >>> instrument = await client.instruments.get(123)
            >>> print(f"Instrument: {instrument.symbol}")
        """
        logger.debug(f"Getting instrument: {instrument_id}")

        response = await self._get(f"/api/v1/instruments/{instrument_id}")

        result = InstrumentResponse(**response)
        logger.info(f"Retrieved instrument: {result.symbol}")
        return result
