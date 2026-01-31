"""Candle (OHLCV) schema."""

from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class Candle(BaseModel):
    """Single candlestick: timestamp and OHLCV.

    Matches CSV format with columns: date, open, high, low, close, volume.
    """

    date: datetime = Field(..., description="Candle timestamp (e.g. 2012-07-02 09:00:00)")
    open: float = Field(..., gt=0, description="Open price")
    high: float = Field(..., gt=0, description="High price")
    low: float = Field(..., gt=0, description="Low price")
    close: float = Field(..., gt=0, description="Close price")
    volume: float = Field(..., ge=0, description="Trading volume")

    @model_validator(mode="after")
    def high_not_below_low(self) -> "Candle":
        """Ensure high >= low."""
        if self.high < self.low:
            raise ValueError(f"❌ high ({self.high}) must be >= low ({self.low})")
        return self
