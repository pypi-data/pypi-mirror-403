"""Support and resistance levels feature generation."""

import logging
from typing import Any

import numpy as np
import pandas as pd
from scipy.signal import argrelextrema

logger = logging.getLogger(__name__)

_REQUIRED_OHLC_COLUMNS = ["open", "high", "low", "close"]


def _validate_ohlc_columns(df: pd.DataFrame, context: str = "") -> None:
    """Validate DataFrame has required OHLC columns.

    Args:
        df: DataFrame to validate.
        context: Optional context for error message.

    Raises:
        ValueError: If any required column is missing.
    """
    missing = set(_REQUIRED_OHLC_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(
            f"❌ Missing required columns: {sorted(missing)}\n"
            f"   Available columns: {sorted(df.columns)}\n"
            f"   Context: {context or 'levels feature'}"
        )


def _levels_dict_to_dataframe(levels_dict: dict) -> pd.DataFrame:
    """Convert levels dict to DataFrame with start_date, end_date, level.

    Args:
        levels_dict: Dict mapping start_date -> (level, end_date).

    Returns:
        DataFrame with columns start_date, end_date, level, sorted by start_date.
    """
    levels_df = pd.DataFrame.from_dict(levels_dict, orient="index", columns=["level", "end_date"])
    levels_df.index.name = "start_date"
    levels_df = levels_df.reset_index().sort_values(by="start_date")
    return levels_df


def _compute_is_support_per_level(df: pd.DataFrame, levels_df: pd.DataFrame) -> pd.Series:
    """Compute whether each level acts as support (True) or resistance (False).

    A level is support when more closes in its range are above the level than below.

    Args:
        df: OHLC DataFrame with datetime index.
        levels_df: DataFrame with columns start_date, end_date, level.

    Returns:
        Boolean Series indexed by levels_df index (True = support, False = resistance).
    """
    is_support_list = []
    for row in levels_df.itertuples():
        end = row.end_date if pd.notna(row.end_date) else df.index[-1]
        valid_close = df.loc[row.start_date : end, "close"]
        below = (valid_close <= row.level).sum()
        above = (valid_close > row.level).sum()
        is_support_list.append(below < above)
    return pd.Series(is_support_list, index=levels_df.index)


def _assign_levels_vectorized(
    df: pd.DataFrame,
    levels_df: pd.DataFrame,
    column_name: str,
) -> pd.DataFrame:
    """Assign support/resistance level to each row using merge_asof (vectorized).

    Args:
        df: OHLC DataFrame; modified in place with new columns.
        levels_df: DataFrame with start_date, end_date, level, is_support.
        column_name: Base name for output columns (e.g. closest_level_10th_order).

    Returns:
        df with columns {column_name}_support and {column_name}_resistance added.
    """
    support_col = f"{column_name}_support"
    resistance_col = f"{column_name}_resistance"
    df[support_col] = np.nan
    df[resistance_col] = np.nan

    if levels_df.empty:
        return df

    levels_sorted = levels_df.sort_values("start_date").copy()
    df_sorted = df.sort_index()
    merged = pd.merge_asof(
        df_sorted,
        levels_sorted,
        left_index=True,
        right_on="start_date",
        direction="backward",
    )
    in_range = (merged.index >= merged["start_date"]) & (
        merged["end_date"].isna() | (merged.index <= merged["end_date"])
    )
    merged[support_col] = np.where(merged["is_support"] & in_range, merged["level"], np.nan)
    merged[resistance_col] = np.where(~merged["is_support"] & in_range, merged["level"], np.nan)
    df[support_col] = merged[support_col].reindex(df.index).values
    df[resistance_col] = merged[resistance_col].reindex(df.index).values
    return df


def generate_levels_feature(
    df: pd.DataFrame,
    order: int,
) -> pd.DataFrame:
    """Create support and resistance level features.

    Args:
        df: DataFrame containing OHLC candle data with datetime index.
        order: Order for local extrema (number of candles per side).

    Returns:
        DataFrame with added columns {column_name}_support and {column_name}_resistance,
        where column_name is closest_level_{order}th_order.
    """
    _validate_ohlc_columns(df, context="generate_levels_feature")
    column_name = f"closest_level_{order}th_order"
    levels_dict = _build_levels(df, order)
    if not levels_dict:
        logger.debug("🔄 No levels found for order=%d, leaving support/resistance empty", order)
        df[f"{column_name}_support"] = np.nan
        df[f"{column_name}_resistance"] = np.nan
        return df

    levels_df = _levels_dict_to_dataframe(levels_dict)
    levels_df["is_support"] = _compute_is_support_per_level(df, levels_df)
    return _assign_levels_vectorized(df, levels_df, column_name)


def _detect_levels(df: pd.DataFrame, order: int = 10) -> dict[Any, tuple[float, Any | None]]:
    """Detect support and resistance levels using local extrema.

    Identifies local minima (support) and maxima (resistance) in price data.
    Ensures intercalation of support and resistance levels.

    Args:
        df: DataFrame with at least 'low' and 'high' and datetime index.
        order: Number of candles to consider for local extrema.

    Returns:
        Dict mapping start_date -> (price_level, None). None reserved for end_date.
    """
    _validate_ohlc_columns(df, context="_detect_levels")
    low_prices = df["low"].to_numpy()
    high_prices = df["high"].to_numpy()
    dates = df.index.to_numpy()

    local_minima = argrelextrema(low_prices, np.less, order=order)[0]
    local_maxima = argrelextrema(high_prices, np.greater, order=order)[0]

    levels = np.concatenate(
        [
            np.column_stack((local_minima, low_prices[local_minima], np.zeros(len(local_minima)))),
            np.column_stack((local_maxima, high_prices[local_maxima], np.ones(len(local_maxima)))),
        ]
    )
    levels = levels[levels[:, 0].argsort()]

    valid_indices = (levels[:, 0] >= order) & (levels[:, 0] < len(df) - order)
    levels = levels[valid_indices.astype(bool)]

    intercalated_levels = _intercalate_levels(levels, low_prices, high_prices)
    if not intercalated_levels.size:
        return {}

    return {dates[int(idx)]: (float(price), None) for idx, price, _ in intercalated_levels}


def _intercalate_levels(
    levels: np.ndarray,
    low_prices: np.ndarray,
    high_prices: np.ndarray,
) -> np.ndarray:
    """Ensure support and resistance levels alternate by inserting intermediate levels.

    Args:
        levels: Array of (index, price, type) with type 0=support, 1=resistance.
        low_prices: Full low price array.
        high_prices: Full high price array.

    Returns:
        Array of intercalated (index, price, type).
    """
    intercalated: list[list[float]] = []
    for i in range(len(levels) - 1):
        current_type = levels[i, 2]
        next_type = levels[i + 1, 2]
        if current_type == next_type:
            start_idx, end_idx = int(levels[i, 0]), int(levels[i + 1, 0])
            if current_type == 0:
                intermediate_idx = np.argmax(high_prices[start_idx:end_idx]) + start_idx
                intercalated.append([float(intermediate_idx), high_prices[intermediate_idx], 1.0])
            else:
                intermediate_idx = np.argmin(low_prices[start_idx:end_idx]) + start_idx
                intercalated.append([float(intermediate_idx), low_prices[intermediate_idx], 0.0])
        intercalated.append(levels[i].tolist())
    if levels.shape[0] > 0:
        intercalated.append(levels[-1].tolist())
    return np.array(intercalated)


def _compute_level_end_dates(
    df: pd.DataFrame,
    levels: dict[Any, tuple[float, Any | None]],
) -> dict[Any, tuple[float, Any | None]]:
    """Compute end date for each level (first price crossing).

    Filters levels by subsequent price action: end_date is when price first
    crosses the level, or None if it never does.

    Args:
        df: DataFrame with 'open' and 'close' and datetime index.
        levels: Dict mapping start_date -> (price_level, None).

    Returns:
        Dict mapping start_date -> (price_level, end_date). end_date is when
        price first crosses the level, or None if never.
    """
    _validate_ohlc_columns(df, context="_compute_level_end_dates")
    open_prices = df["open"].to_numpy()
    close_prices = df["close"].to_numpy()
    dates = df.index.to_numpy()

    filtered_levels: dict[Any, tuple[float, Any | None]] = {}
    for date, (price, _) in levels.items():
        idx = np.searchsorted(dates, date)
        future_open = open_prices[idx + 1 :]
        future_close = close_prices[idx + 1 :]
        crossing = (future_open > price) & (future_close < price) | (
            (future_open < price) & (future_close > price)
        )
        filtered_idx = np.argmax(crossing) if crossing.any() else None
        filtered_date = dates[idx + 1 + filtered_idx] if filtered_idx is not None else None
        filtered_levels[date] = (price, filtered_date)
    return filtered_levels


def _offset_levels(
    df: pd.DataFrame,
    levels: dict[Any, tuple[float, Any | None]],
    order: int,
) -> dict[Any, tuple[float, Any | None]]:
    """Offset level start dates by order candles.

    Args:
        df: DataFrame with datetime index.
        levels: Dict mapping start_date -> (price_level, end_date).
        order: Number of candles to offset.

    Returns:
        Dict mapping (offset) start_date -> (price_level, end_date).
    """
    dates = df.index.to_numpy()
    result: dict[Any, tuple[float, Any | None]] = {}
    previous_end_date: Any | None = None

    for start_date, (value, end_date) in levels.items():
        idx = np.searchsorted(dates, start_date)
        offset_idx = min(idx + order, len(dates) - 1)
        offset_date = dates[offset_idx]

        if previous_end_date is not None and offset_date > previous_end_date:
            result[previous_end_date] = (value, end_date)
        else:
            result[offset_date] = (value, end_date)
        previous_end_date = end_date
    return result


def _build_levels(df: pd.DataFrame, order: int = 10) -> dict[Any, tuple[float, Any | None]]:
    """Build levels pipeline: detect, compute end dates, then offset.

    Args:
        df: DataFrame with OHLC and datetime index.
        order: Order for local extrema and offset.

    Returns:
        Dict mapping start_date -> (price_level, end_date). Empty dict if no levels.
    """
    _validate_ohlc_columns(df, context="_build_levels")
    levels_dict = _detect_levels(df, order)
    if not levels_dict:
        return {}
    levels_dict = _compute_level_end_dates(df, levels_dict)
    levels_dict = _offset_levels(df, levels_dict, order)
    return levels_dict
