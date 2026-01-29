"""
Blueprint 鏈式建構器

支援鏈式添加 entry/exit triggers，最後透過 .build() 回傳 BlueprintConfig。

Usage:
    from tradepose_client.builder import BlueprintBuilder, TradingContext
    import polars as pl

    # 建立 Base Blueprint
    base_bp = BlueprintBuilder(
        name="base_trend",
        direction="Long",
        trend_type="Trend",
        note="基礎趨勢策略"
    ).add_entry_trigger(
        name="entry",
        conditions=[pl.col("ema_20") > pl.col("ema_50")],
        price_expr=pl.col("open"),
        order_strategy="ImmediateEntry",
        priority=1,
        note="EMA 金叉"
    ).add_exit_trigger(
        name="exit",
        conditions=[pl.col("ema_20") < pl.col("ema_50")],
        price_expr=pl.col("open"),
        order_strategy="ImmediateExit",
        priority=1,
        note="EMA 死叉"
    ).build()

    # 建立 Advanced Blueprint
    adv_bp = BlueprintBuilder("risk_mgmt", "Long", "Trend")\
        .add_exit_trigger(
            name="stop_loss",
            conditions=[],
            price_expr=TradingContext.advanced_entry.entry_price - pl.col("atr") * 2,
            order_strategy="StopLoss",
            priority=1
        )\
        .add_exit_trigger(
            name="take_profit",
            conditions=[],
            price_expr=TradingContext.advanced_entry.entry_price + pl.col("atr") * 3,
            order_strategy="TakeProfit",
            priority=2
        )\
        .build()
"""

from typing import TYPE_CHECKING, List, Union

import polars as pl

if TYPE_CHECKING:
    from tradepose_models.enums import OrderStrategy, TradeDirection, TrendType
    from tradepose_models.strategy import Blueprint, Trigger


class BlueprintBuilder:
    """
    Blueprint 鏈式建構器

    支援鏈式添加 entry/exit triggers，提供流暢的 API 體驗。

    Attributes:
        name (str): Blueprint 名稱
        direction (str): 交易方向（"Long", "Short", "Both"）
        trend_type (str): 趨勢類型（"Trend", "Range", "Reversal"）
        entry_first (bool): 是否必須先進場才能出場
        note (str): 備註

    Methods:
        add_entry_trigger(...) -> BlueprintBuilder: 添加進場觸發器（鏈式）
        add_exit_trigger(...) -> BlueprintBuilder: 添加出場觸發器（鏈式）
        build() -> Blueprint: 建構最終 Blueprint 物件
    """

    def __init__(
        self,
        name: str,
        direction: Union["TradeDirection", str],
        trend_type: Union["TrendType", str] = "Trend",
        entry_first: bool = True,
        note: str = "",
    ):
        """
        初始化 Blueprint 建構器

        Args:
            name: Blueprint 名稱（唯一標識）
            direction: 交易方向
                - "Long": 做多
                - "Short": 做空
                - "Both": 雙向（暫不支援）
            trend_type: 趨勢類型
                - "Trend": 趨勢跟隨
                - "Range": 區間震盪
                - "Reversal": 反轉交易
            entry_first: 是否必須先進場才能出場（推薦 True）
            note: Blueprint 說明

        Examples:
            >>> # Base Blueprint（簡潔形式）
            >>> bp = BlueprintBuilder("base", "Long", "Trend")
            >>>
            >>> # Advanced Blueprint（完整形式）
            >>> adv_bp = BlueprintBuilder(
            ...     name="risk_management",
            ...     direction="Long",
            ...     trend_type="Trend",
            ...     entry_first=True,
            ...     note="Stop Loss + Take Profit"
            ... )
        """
        self.name = name
        self.direction = direction
        self.trend_type = trend_type
        self.entry_first = entry_first
        self.note = note

        self._entry_triggers: List["Trigger"] = []
        self._exit_triggers: List["Trigger"] = []

    def add_entry_trigger(
        self,
        name: str,
        conditions: List[pl.Expr],
        price_expr: pl.Expr,
        order_strategy: Union["OrderStrategy", str],
        priority: int = 1,
        note: str = "",
    ) -> "BlueprintBuilder":
        """
        添加進場觸發器（鏈式呼叫）

        Args:
            name: 觸發器名稱（唯一標識）
            conditions: 條件表達式列表（全部為 True 才觸發）
            price_expr: 價格表達式（Polars Expr）
            order_strategy: 訂單策略
                - Base Blueprint 必須使用 "ImmediateEntry"
                - Advanced Blueprint 可使用 "FavorableDelayEntry", "AdverseDelayEntry" 等
            priority: 優先級（1-100，越小優先級越高，預設 1）
            note: 觸發器說明

        Returns:
            BlueprintBuilder: 回傳自身，支援鏈式呼叫

        Examples:
            >>> bp = BlueprintBuilder("base", "Long", "Trend")\
            ...     .add_entry_trigger(
            ...         name="entry",
            ...         conditions=[pl.col("ema_20") > pl.col("ema_50")],
            ...         price_expr=pl.col("open"),
            ...         order_strategy="ImmediateEntry",
            ...         note="EMA 金叉"
            ...     )
        """
        from tradepose_models.strategy import create_trigger

        trigger = create_trigger(
            name=name,
            conditions=conditions,
            price_expr=price_expr,
            order_strategy=order_strategy,
            priority=priority,
            note=note,
        )
        self._entry_triggers.append(trigger)
        return self

    def add_exit_trigger(
        self,
        name: str,
        conditions: List[pl.Expr],
        price_expr: pl.Expr,
        order_strategy: Union["OrderStrategy", str],
        priority: int = 1,
        note: str = "",
    ) -> "BlueprintBuilder":
        """
        添加出場觸發器（鏈式呼叫）

        Args:
            name: 觸發器名稱（唯一標識）
            conditions: 條件表達式列表（全部為 True 才觸發）
            price_expr: 價格表達式（Polars Expr）
            order_strategy: 訂單策略
                - Base Blueprint 必須使用 "ImmediateExit"
                - Advanced Blueprint 可使用 "StopLoss", "TakeProfit", "TrailingStop",
                  "Breakeven", "TimeoutExit" 等
            priority: 優先級（1-100，越小優先級越高，預設 1）
            note: 觸發器說明

        Returns:
            BlueprintBuilder: 回傳自身，支援鏈式呼叫

        Examples:
            >>> bp = BlueprintBuilder("risk_mgmt", "Long", "Trend")\
            ...     .add_exit_trigger(
            ...         name="stop_loss",
            ...         conditions=[],
            ...         price_expr=TradingContext.advanced_entry.entry_price - pl.col("atr") * 2,
            ...         order_strategy="StopLoss",
            ...         note="固定止損 2 ATR"
            ...     )\
            ...     .add_exit_trigger(
            ...         name="take_profit",
            ...         conditions=[],
            ...         price_expr=TradingContext.advanced_entry.entry_price + pl.col("atr") * 3,
            ...         order_strategy="TakeProfit",
            ...         note="目標止盈 3 ATR"
            ...     )
        """
        from tradepose_models.strategy import create_trigger

        trigger = create_trigger(
            name=name,
            conditions=conditions,
            price_expr=price_expr,
            order_strategy=order_strategy,
            priority=priority,
            note=note,
        )
        self._exit_triggers.append(trigger)
        return self

    def build(self) -> "Blueprint":
        """
        建構最終 Blueprint 物件

        Returns:
            Blueprint: 完整的 Blueprint 設定物件

        Raises:
            ValueError: 如果未添加任何 trigger

        Examples:
            >>> bp = BlueprintBuilder("base", "Long", "Trend")\
            ...     .add_entry_trigger(...)\
            ...     .add_exit_trigger(...)\
            ...     .build()
            >>>
            >>> # 用於 StrategyBuilder
            >>> builder.set_base_blueprint(bp)
            >>> builder.add_advanced_blueprint(adv_bp)
        """
        from tradepose_models.strategy import create_blueprint

        if not self._entry_triggers and not self._exit_triggers:
            raise ValueError(
                f"Blueprint '{self.name}' must have at least one entry or exit trigger. "
                f"Use .add_entry_trigger() or .add_exit_trigger() before calling .build()"
            )

        return create_blueprint(
            name=self.name,
            direction=self.direction,
            entry_triggers=self._entry_triggers,
            exit_triggers=self._exit_triggers,
            trend_type=self.trend_type,
            entry_first=self.entry_first,
            note=self.note,
        )

    def __repr__(self) -> str:
        """字串表示"""
        return (
            f"BlueprintBuilder(name='{self.name}', "
            f"direction='{self.direction}', "
            f"entry_triggers={len(self._entry_triggers)}, "
            f"exit_triggers={len(self._exit_triggers)})"
        )
