"""Slots resource for TradePose Client.

This module provides operations for managing trader slot bindings.
"""

import logging
from datetime import datetime

from pydantic import BaseModel, Field

from .base import BaseResource

logger = logging.getLogger(__name__)


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================


class SlotBindRequest(BaseModel):
    """Request body for binding an account to a slot."""

    account_id: str = Field(..., description="Account ID to bind")


class SlotResponse(BaseModel):
    """Slot binding response."""

    id: str
    user_id: str
    node_seq: int
    slot_idx: int
    account_id: str | None = None
    bound_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class SlotListResponse(BaseModel):
    """List of slots response."""

    slots: list[SlotResponse]
    total: int


# =============================================================================
# RESOURCE CLASS
# =============================================================================


class SlotsResource(BaseResource):
    """Slot management resource.

    Provides operations for managing trader slot bindings.
    Slots are pre-registered by the Trader service deployment.

    Example:
        >>> async with TradePoseClient(api_key="tp_live_xxx") as client:
        ...     # List all slots
        ...     slots = await client.slots.list()
        ...     print(f"Found {slots.total} slots")
        ...
        ...     # Bind account to slot
        ...     slot = await client.slots.bind(0, 0, account_id="uuid")
        ...
        ...     # Unbind account from slot
        ...     slot = await client.slots.unbind(0, 0)
    """

    async def list(self) -> SlotListResponse:
        """List all slots for the authenticated user.

        Returns:
            List of slots with their binding status

        Raises:
            TradePoseAPIError: For API errors

        Example:
            >>> slots = await client.slots.list()
            >>> for slot in slots.slots:
            ...     print(f"Slot {slot.node_seq}/{slot.slot_idx}: {slot.account_id}")
        """
        logger.debug("Listing slots")

        response = await self._get("/api/v1/slots")

        result = SlotListResponse(**response)
        logger.info(f"Listed {result.total} slots")
        return result

    async def get(self, node_seq: int, slot_idx: int) -> SlotResponse:
        """Get a specific slot by node_seq and slot_idx.

        Args:
            node_seq: Node sequence number (0-based)
            slot_idx: Slot index within the node (0-based)

        Returns:
            Slot details

        Raises:
            ResourceNotFoundError: If slot not found
            TradePoseAPIError: For other API errors

        Example:
            >>> slot = await client.slots.get(0, 0)
            >>> print(f"Slot bound to: {slot.account_id}")
        """
        logger.debug(f"Getting slot: node_seq={node_seq}, slot_idx={slot_idx}")

        response = await self._get(f"/api/v1/slots/{node_seq}/{slot_idx}")

        result = SlotResponse(**response)
        logger.info(f"Retrieved slot: {result.node_seq}/{result.slot_idx}")
        return result

    async def bind(
        self,
        node_seq: int,
        slot_idx: int,
        account_id: str,
    ) -> SlotResponse:
        """Bind an account to a slot.

        Creates the slot if it doesn't exist, then binds the account.
        Publishes a bind event to notify the Trader service.

        Args:
            node_seq: Node sequence number (0-based)
            slot_idx: Slot index within the node (0-based)
            account_id: Account UUID to bind

        Returns:
            Updated slot with bound account

        Raises:
            ValidationError: If account_id is invalid
            TradePoseAPIError: For other API errors

        Example:
            >>> slot = await client.slots.bind(0, 0, account_id="uuid-here")
            >>> print(f"Slot bound at: {slot.bound_at}")
        """
        logger.info(f"Binding slot: node_seq={node_seq}, slot_idx={slot_idx}, account={account_id}")

        response = await self._post(
            f"/api/v1/slots/{node_seq}/{slot_idx}/bind",
            json={"account_id": account_id},
        )

        result = SlotResponse(**response)
        logger.info(f"Slot bound: {result.node_seq}/{result.slot_idx} -> {result.account_id}")
        return result

    async def unbind(
        self,
        node_seq: int,
        slot_idx: int,
    ) -> SlotResponse:
        """Unbind an account from a slot.

        Publishes an unbind event to notify the Trader service.

        Args:
            node_seq: Node sequence number (0-based)
            slot_idx: Slot index within the node (0-based)

        Returns:
            Updated slot with account unbound

        Raises:
            ResourceNotFoundError: If slot not found
            TradePoseAPIError: For other API errors

        Example:
            >>> slot = await client.slots.unbind(0, 0)
            >>> assert slot.account_id is None
        """
        logger.info(f"Unbinding slot: node_seq={node_seq}, slot_idx={slot_idx}")

        response = await self._post(f"/api/v1/slots/{node_seq}/{slot_idx}/unbind")

        result = SlotResponse(**response)
        logger.info(f"Slot unbound: {result.node_seq}/{result.slot_idx}")
        return result
