"""Strategy resource for TradePose Client (StrategyConfig-centric).

This module provides synchronous CRUD operations for complete strategy configurations.
Treats StrategyConfig (strategy + blueprints) as an atomic unit.

Uses tradepose_models.strategy.StrategyConfig as the unified response model.
"""

import logging

from pydantic import BaseModel
from tradepose_models.enums import Freq
from tradepose_models.indicators import PolarsExprField
from tradepose_models.strategy import StrategyConfig

from .base import BaseResource

logger = logging.getLogger(__name__)


# =============================================================================
# LIST RESPONSE MODELS (metadata only, no full config)
# =============================================================================


class BlueprintInfo(BaseModel):
    """Blueprint identifier with id and name."""

    id: str
    name: str


class StrategyListItemResponse(BaseModel):
    """Strategy list item response (metadata only)."""

    id: str
    name: str
    base_instrument: str
    base_freq: str
    note: str
    base_blueprint: BlueprintInfo
    advanced_blueprints: list[BlueprintInfo]


class StrategyListResponse(BaseModel):
    """Strategy list response."""

    strategies: list[StrategyListItemResponse]
    count: int


# =============================================================================
# RESOURCE CLASS
# =============================================================================


class StrategiesResource(BaseResource):
    """Strategy CRUD resource (StrategyConfig-centric).

    Provides synchronous operations for managing complete strategy configurations.
    All operations treat StrategyConfig as an atomic unit containing strategy
    metadata and all blueprints (base + advanced).

    Example:
        >>> from tradepose_models.strategy import StrategyConfig, Blueprint
        >>> from tradepose_models.enums import Freq, TradeDirection, TrendType
        >>>
        >>> async with TradePoseClient(api_key="tp_live_xxx") as client:
        ...     # Create complete strategy configuration
        ...     config = StrategyConfig(
        ...         name="my_strategy",
        ...         base_instrument="BTCUSDT",
        ...         base_freq=Freq.MIN_15,
        ...         note="Example strategy",
        ...         volatility_indicator=None,
        ...         indicators=[],
        ...         base_blueprint=Blueprint(
        ...             name="base",
        ...             direction=TradeDirection.LONG,
        ...             trend_type=TrendType.TREND,
        ...             entry_first=True,
        ...             note="Base blueprint",
        ...             entry_triggers=[],
        ...             exit_triggers=[],
        ...         ),
        ...         advanced_blueprints=[],
        ...     )
        ...
        ...     # Create or update (upsert)
        ...     result = await client.strategies.create(config)
        ...
        ...     # List all strategies (metadata only)
        ...     strategies = await client.strategies.list()
        ...
        ...     # Get complete configuration
        ...     strategy = await client.strategies.get("my_strategy")
        ...
        ...     # Delete strategy (cascades to blueprints)
        ...     await client.strategies.delete("my_strategy")
    """

    async def create(self, config: StrategyConfig) -> StrategyConfig:
        """Create or get existing strategy configuration (get-or-create).

        If strategy name exists, returns existing strategy unchanged.
        To replace a strategy, delete it first and recreate.

        Args:
            config: Complete StrategyConfig (strategy + all blueprints)

        Returns:
            Complete StrategyConfig (with id from database)

        Raises:
            ValidationError: If config data is invalid
            TradePoseAPIError: For other API errors

        Example:
            >>> config = StrategyConfig(
            ...     name="my_strategy",
            ...     base_instrument="BTCUSDT",
            ...     base_freq=Freq.MIN_15,
            ...     note="Example",
            ...     volatility_indicator=None,
            ...     indicators=[],
            ...     base_blueprint=Blueprint(...),
            ...     advanced_blueprints=[],
            ... )
            >>> result = await client.strategies.create(config)
            >>> print(f"Strategy: {result.name} (id: {result.id})")
        """
        logger.info(f"Creating strategy: {config.name}")

        # Convert StrategyConfig to request format
        request_data = {
            "name": config.name,
            "base_instrument": config.base_instrument,
            "base_freq": config.base_freq.value
            if isinstance(config.base_freq, Freq)
            else config.base_freq,
            "note": config.note,
            "volatility_indicator": PolarsExprField.serialize(config.volatility_indicator)
            if config.volatility_indicator is not None
            else None,
            "indicators": [ind.model_dump() for ind in config.indicators],
            "base_blueprint": config.base_blueprint.model_dump(),
            "advanced_blueprints": [bp.model_dump() for bp in config.advanced_blueprints],
        }

        response = await self._post("/api/v1/strategies", json=request_data)

        result = StrategyConfig.from_api(response)
        logger.info(f"Strategy: {result.name} (id: {result.id})")
        return result

    async def list(self, *, archived: bool = False) -> StrategyListResponse:
        """List all strategies (metadata only).

        Args:
            archived: If True, include archived strategies. Defaults to False.

        Returns:
            List of strategy metadata

        Raises:
            TradePoseAPIError: For API errors

        Example:
            >>> strategies = await client.strategies.list()
            >>> print(f"Found {strategies.count} strategies")
            >>> for s in strategies.strategies:
            ...     print(f"  - {s.name} ({s.base_instrument})")
        """
        logger.debug("Listing strategies")

        response = await self._get(
            "/api/v1/strategies",
            params={"archived": str(archived).lower()},
        )

        result = StrategyListResponse(**response)
        logger.info(f"Listed {result.count} strategies")
        return result

    async def get(self, strategy_id: str) -> StrategyConfig:
        """Get complete strategy configuration by ID.

        Args:
            strategy_id: Strategy UUID

        Returns:
            Complete StrategyConfig (with id from database)

        Raises:
            ResourceNotFoundError: If strategy not found
            TradePoseAPIError: For other API errors

        Example:
            >>> strategy = await client.strategies.get("550e8400-e29b-41d4-a716-446655440000")
            >>> print(f"Strategy: {strategy.name} (id: {strategy.id})")
            >>> print(f"Base blueprint: {strategy.base_blueprint.name}")
            >>> print(f"Advanced blueprints: {len(strategy.advanced_blueprints)}")
        """
        logger.debug(f"Getting strategy by id: {strategy_id}")

        response = await self._get(f"/api/v1/strategies/{strategy_id}")

        result = StrategyConfig.from_api(response)
        logger.info(f"Retrieved strategy: {result.name} (id: {result.id})")
        return result

    async def delete(self, name: str, *, archive: bool = True) -> dict:
        """Delete strategy (cascades to blueprints).

        Args:
            name: Strategy name
            archive: If True, soft-delete (archive). If False, hard delete.
                     Defaults to True (soft delete).

        Returns:
            Success message

        Raises:
            ResourceNotFoundError: If strategy not found
            TradePoseAPIError: For other API errors

        Example:
            >>> # Soft delete (archive)
            >>> response = await client.strategies.delete("my_strategy")
            >>> print(response["message"])  # "Strategy 'my_strategy' archived"
            >>>
            >>> # Hard delete (permanent)
            >>> response = await client.strategies.delete("my_strategy", archive=False)
            >>> print(response["message"])  # "Strategy 'my_strategy' deleted"
        """
        from urllib.parse import quote

        action = "Archiving" if archive else "Deleting"
        logger.info(f"{action} strategy: {name}")

        # URL encode name to handle special characters like '.'
        encoded_name = quote(name, safe="")
        response = await self._delete(
            f"/api/v1/strategies/{encoded_name}",
            params={"archive": str(archive).lower()},
        )

        result_action = "archived" if archive else "deleted"
        logger.info(f"Strategy {name} {result_action}")
        return response  # type: ignore
