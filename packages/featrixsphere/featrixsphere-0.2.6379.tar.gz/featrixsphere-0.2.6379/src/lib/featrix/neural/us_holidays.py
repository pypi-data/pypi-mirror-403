#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential. Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
"""
US Holiday Detection - Vectorized PyTorch Implementation

Provides GPU-accelerated holiday detection for temporal feature engineering.
All computations are vectorized for batch processing without Python loops.

Supported Holidays:
- Fixed-date: New Year's Day, Independence Day, Veterans Day, Christmas
- Floating: MLK Day, Presidents Day, Memorial Day, Labor Day,
           Columbus Day, Thanksgiving
- Bonus: Christmas Eve, New Year's Eve, Black Friday
"""
import torch
from typing import Tuple


# =============================================================================
# Fixed-Date Holidays (month, day)
# =============================================================================
FIXED_HOLIDAYS = [
    (1, 1),    # New Year's Day
    (7, 4),    # Independence Day
    (11, 11),  # Veterans Day
    (12, 25),  # Christmas Day
    (12, 24),  # Christmas Eve
    (12, 31),  # New Year's Eve
]


def _nth_weekday_of_month(
    year: torch.Tensor,
    month: int,
    weekday: int,  # 0=Monday, 6=Sunday
    n: int,  # 1st, 2nd, 3rd, 4th
) -> torch.Tensor:
    """
    Compute the day-of-month for the nth occurrence of a weekday in a month.

    Uses Zeller's congruence to find the first occurrence of the weekday,
    then adds (n-1) * 7 days.

    Args:
        year: Tensor of years (batch,)
        month: Month number (1-12)
        weekday: Target weekday (0=Monday, 6=Sunday)
        n: Which occurrence (1=first, 2=second, etc.)

    Returns:
        Tensor of day-of-month values (batch,)
    """
    # Find day-of-week for the 1st of the month using Zeller's congruence
    # Adjusted for Monday=0 convention
    y = year.clone()
    m = torch.full_like(year, month)

    # Zeller adjustment: Jan/Feb are months 13/14 of previous year
    mask = m <= 2
    y = torch.where(mask, y - 1, y)
    m = torch.where(mask, m + 12, m)

    # Zeller's congruence for Gregorian calendar
    # h = (1 + floor(13*(m+1)/5) + K + floor(K/4) + floor(J/4) - 2*J) mod 7
    # where K = year % 100, J = year // 100
    K = y % 100
    J = y // 100

    h = (1 + (13 * (m + 1)) // 5 + K + K // 4 + J // 4 - 2 * J) % 7
    # h: 0=Saturday, 1=Sunday, 2=Monday, ..., 6=Friday
    # Convert to Monday=0 convention
    dow_first = (h + 5) % 7  # Now 0=Monday, 6=Sunday

    # Days until first occurrence of target weekday
    days_until = (weekday - dow_first) % 7

    # Day of month for first occurrence
    first_occurrence = 1 + days_until

    # Add weeks for nth occurrence
    return first_occurrence + (n - 1) * 7


def _last_weekday_of_month(
    year: torch.Tensor,
    month: int,
    weekday: int,  # 0=Monday, 6=Sunday
) -> torch.Tensor:
    """
    Compute the day-of-month for the last occurrence of a weekday in a month.

    Args:
        year: Tensor of years (batch,)
        month: Month number (1-12)
        weekday: Target weekday (0=Monday, 6=Sunday)

    Returns:
        Tensor of day-of-month values (batch,)
    """
    # Days in each month (non-leap year base)
    days_in_month = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    base_days = days_in_month[month]

    # Handle February in leap years
    if month == 2:
        is_leap = ((year % 4 == 0) & ((year % 100 != 0) | (year % 400 == 0)))
        last_day = torch.where(is_leap, torch.tensor(29, device=year.device),
                               torch.tensor(28, device=year.device))
    else:
        last_day = torch.full_like(year, base_days)

    # Find day-of-week for last day of month using Zeller's
    y = year.clone()
    m = torch.full_like(year, month)
    d = last_day

    mask = m <= 2
    y = torch.where(mask, y - 1, y)
    m = torch.where(mask, m + 12, m)

    K = y % 100
    J = y // 100
    h = (d + (13 * (m + 1)) // 5 + K + K // 4 + J // 4 - 2 * J) % 7
    dow_last = (h + 5) % 7  # Monday=0 convention

    # Days to go back to find the target weekday
    days_back = (dow_last - weekday) % 7

    return last_day - days_back


def compute_floating_holidays(year: torch.Tensor) -> dict:
    """
    Compute all floating US holidays for given years.

    Args:
        year: Tensor of years (batch,)

    Returns:
        Dict mapping holiday name to (month, day_of_month) tensors
    """
    device = year.device

    return {
        # MLK Day: 3rd Monday of January
        'mlk_day': (1, _nth_weekday_of_month(year, 1, 0, 3)),

        # Presidents Day: 3rd Monday of February
        'presidents_day': (2, _nth_weekday_of_month(year, 2, 0, 3)),

        # Memorial Day: Last Monday of May
        'memorial_day': (5, _last_weekday_of_month(year, 5, 0)),

        # Labor Day: 1st Monday of September
        'labor_day': (9, _nth_weekday_of_month(year, 9, 0, 1)),

        # Columbus Day: 2nd Monday of October
        'columbus_day': (10, _nth_weekday_of_month(year, 10, 0, 2)),

        # Thanksgiving: 4th Thursday of November
        'thanksgiving': (11, _nth_weekday_of_month(year, 11, 3, 4)),
    }


def is_us_holiday(
    year: torch.Tensor,
    month: torch.Tensor,
    day_of_month: torch.Tensor,
) -> torch.Tensor:
    """
    Check if dates are US holidays.

    Args:
        year: Tensor of years (batch,)
        month: Tensor of months 1-12 (batch,)
        day_of_month: Tensor of days 1-31 (batch,)

    Returns:
        Boolean tensor (batch,) - True if date is a US holiday
    """
    device = year.device
    batch_size = year.shape[0]

    # Ensure integer types for comparison
    month = month.round().long()
    day_of_month = day_of_month.round().long()
    year = year.round().long()

    # Start with all False
    is_holiday = torch.zeros(batch_size, dtype=torch.bool, device=device)

    # Check fixed-date holidays
    for h_month, h_day in FIXED_HOLIDAYS:
        is_holiday = is_holiday | ((month == h_month) & (day_of_month == h_day))

    # Check floating holidays
    floating = compute_floating_holidays(year)
    for name, (h_month, h_day_tensor) in floating.items():
        is_holiday = is_holiday | ((month == h_month) & (day_of_month == h_day_tensor))

    # Black Friday: day after Thanksgiving
    thanksgiving_month, thanksgiving_day = floating['thanksgiving']
    is_holiday = is_holiday | ((month == 11) & (day_of_month == thanksgiving_day + 1))

    return is_holiday


def compute_holiday_distances(
    year: torch.Tensor,
    day_of_year: torch.Tensor,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Compute days until next holiday and days since last holiday.

    This is an approximation using day-of-year for efficiency.
    For dates near year boundaries, the approximation may be off by a few days.

    Args:
        year: Tensor of years (batch,)
        day_of_year: Tensor of day-of-year 1-366 (batch,)

    Returns:
        Tuple of:
        - days_to_next: Days until next major holiday (0 if today is holiday)
        - days_since_last: Days since last major holiday (0 if today is holiday)
    """
    device = year.device
    batch_size = year.shape[0]
    year = year.round().long()
    doy = day_of_year.round().long()

    # Approximate day-of-year for fixed holidays (ignoring leap year for simplicity)
    # Jan 1 = 1, Jul 4 = 185, Nov 11 = 315, Dec 25 = 359
    fixed_doys = torch.tensor([1, 185, 315, 359], device=device)

    # Get floating holidays for this year
    floating = compute_floating_holidays(year)

    # Compute approximate DOY for floating holidays
    # DOY = (month-1)*30.5 + day (rough approximation)
    floating_doys = []
    for name, (h_month, h_day_tensor) in floating.items():
        approx_doy = (h_month - 1) * 30 + h_month // 2 + h_day_tensor
        floating_doys.append(approx_doy)

    # Stack all holiday DOYs: (batch, n_floating)
    floating_doys = torch.stack(floating_doys, dim=1)  # (batch, 6)

    # Expand fixed holidays: (batch, n_fixed)
    fixed_expanded = fixed_doys.unsqueeze(0).expand(batch_size, -1)

    # All holidays: (batch, n_total)
    all_holiday_doys = torch.cat([fixed_expanded, floating_doys], dim=1)

    # Compute distances to all holidays
    # doy: (batch, 1), all_holiday_doys: (batch, n_holidays)
    doy_expanded = doy.unsqueeze(1)  # (batch, 1)

    # Forward distance (days until holiday, wrapping around year)
    forward_dist = (all_holiday_doys - doy_expanded) % 365
    forward_dist = torch.where(forward_dist == 0,
                               torch.zeros_like(forward_dist),
                               forward_dist)

    # Backward distance (days since holiday, wrapping around year)
    backward_dist = (doy_expanded - all_holiday_doys) % 365
    backward_dist = torch.where(backward_dist == 0,
                                torch.zeros_like(backward_dist),
                                backward_dist)

    # Find minimum distances
    days_to_next = forward_dist.min(dim=1).values
    days_since_last = backward_dist.min(dim=1).values

    # Check if today is a holiday (set distances to 0)
    # For simplicity, check if min forward or backward is very small
    # This handles the case where doy matches a holiday doy
    exact_match = (all_holiday_doys == doy_expanded).any(dim=1)
    days_to_next = torch.where(exact_match, torch.zeros_like(days_to_next), days_to_next)
    days_since_last = torch.where(exact_match, torch.zeros_like(days_since_last), days_since_last)

    return days_to_next.float(), days_since_last.float()


def get_holiday_features(
    year: torch.Tensor,
    month: torch.Tensor,
    day_of_month: torch.Tensor,
    day_of_year: torch.Tensor,
    max_holiday_distance: int = 30,
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Compute all holiday-related features.

    Args:
        year: Tensor of years (batch,)
        month: Tensor of months 1-12 (batch,)
        day_of_month: Tensor of days 1-31 (batch,)
        day_of_year: Tensor of day-of-year 1-366 (batch,)
        max_holiday_distance: Cap distance values at this number of days

    Returns:
        Tuple of:
        - is_holiday: Binary tensor (batch,) - 1.0 if holiday
        - days_to_next: Normalized days until next holiday (batch,)
        - days_since_last: Normalized days since last holiday (batch,)
    """
    # Check if holiday
    is_holiday = is_us_holiday(year, month, day_of_month).float()

    # Compute distances
    days_to_next, days_since_last = compute_holiday_distances(year, day_of_year)

    # Cap and normalize distances
    days_to_next = days_to_next.clamp(0, max_holiday_distance) / max_holiday_distance
    days_since_last = days_since_last.clamp(0, max_holiday_distance) / max_holiday_distance

    return is_holiday, days_to_next, days_since_last
