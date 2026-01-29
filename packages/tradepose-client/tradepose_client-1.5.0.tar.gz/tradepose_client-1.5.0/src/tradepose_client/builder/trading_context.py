"""
Trading Context 固定欄位存取器

基於 schema.py 中定義的 struct 欄位，提供簡潔的屬性存取方式，
避免繁瑣的 `.struct.field()` 呼叫。

Usage:
    from tradepose_client.builder import TradingContext
    import polars as pl

    # 簡潔存取（返回 pl.Expr）
    entry_price = TradingContext.base.entry_price
    highest = TradingContext.advanced_entry.highest_since_entry
    bars = TradingContext.advanced_exit.bars_since_entry

    # 用於策略條件表達式
    condition = TradingContext.base.bars_in_position > 50
    stop_loss_price = TradingContext.advanced_entry.entry_price - pl.col("atr") * 2
"""

import polars as pl


class TradingContextProxy:
    """
    Trading Context 欄位存取代理

    為 base_trading_context, advanced_entry_trading_context,
    advanced_exit_trading_context 提供統一的屬性存取介面。

    Args:
        context_name: 上下文欄位名稱（如 "base_trading_context"）
    """

    def __init__(
        self,
        context_name: str,
    ):
        self._context_name = context_name

    @property
    def entry_price(self) -> pl.Expr:
        """
        進場價格

        Returns:
            pl.Expr: Polars 表達式，可直接用於條件或價格計算
        """
        return pl.col(self._context_name).struct.field("position_entry_price")

    @property
    def bars_in_position(self) -> pl.Expr:
        """
        持倉 K 線數

        Returns:
            pl.Expr: Polars 表達式

        Note:
            Rust worker 統一使用 "bars_since_entry" 欄位名稱
        """
        return pl.col(self._context_name).struct.field("bars_since_entry")

    @property
    def bars_since_entry(self) -> pl.Expr:
        """
        進場以來 K 線數（bars_in_position 的別名）

        Returns:
            pl.Expr: Polars 表達式
        """
        return self.bars_in_position

    @property
    def highest_since_entry(self) -> pl.Expr:
        """
        進場以來最高價

        Returns:
            pl.Expr: Polars 表達式，可用於 trailing stop 計算

        Note:
            Rust worker 統一使用 "highest_since_entry" 欄位名稱
        """
        return pl.col(self._context_name).struct.field("highest_since_entry")

    @property
    def lowest_since_entry(self) -> pl.Expr:
        """
        進場以來最低價

        Returns:
            pl.Expr: Polars 表達式，可用於 short position trailing stop 計算

        Note:
            Rust worker 統一使用 "lowest_since_entry" 欄位名稱
        """
        return pl.col(self._context_name).struct.field("lowest_since_entry")


class TradingContext:
    """
    Trading Context 統一存取器

    提供三種 trading context 的屬性存取：
    - base: base_trading_context
    - advanced_entry: advanced_entry_trading_context
    - advanced_exit: advanced_exit_trading_context

    Usage:
        # Base context（Base Blueprint 生成）
        TradingContext.base.entry_price
        TradingContext.base.bars_in_position
        TradingContext.base.highest_since_entry
        TradingContext.base.lowest_since_entry

        # Advanced Entry context（Advanced Entry Triggers 使用）
        TradingContext.advanced_entry.entry_price
        TradingContext.advanced_entry.bars_since_entry
        TradingContext.advanced_entry.highest_since_entry
        TradingContext.advanced_entry.lowest_since_entry

        # Advanced Exit context（Advanced Exit Triggers 使用）
        TradingContext.advanced_exit.entry_price
        TradingContext.advanced_exit.bars_since_entry
        TradingContext.advanced_exit.highest_since_entry
        TradingContext.advanced_exit.lowest_since_entry

    Examples:
        # Stop Loss（Long）
        stop_loss_price = (
            TradingContext.advanced_entry.entry_price -
            pl.col("atr") * 2
        )

        # Trailing Stop（Long）
        trailing_stop_price = (
            TradingContext.advanced_entry.highest_since_entry -
            pl.col("atr") * 2
        )

        # 持倉時間過濾
        timeout_condition = TradingContext.advanced_entry.bars_since_entry > 100
    """

    base = TradingContextProxy("base_trading_context")
    advanced_entry = TradingContextProxy("advanced_entry_trading_context")
    advanced_exit = TradingContextProxy("advanced_exit_trading_context")


# 向後相容的別名
BaseContext = TradingContext.base
AdvancedEntryContext = TradingContext.advanced_entry
AdvancedExitContext = TradingContext.advanced_exit
