from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal, getcontext

from ..utils.constants import BASIS_POINT_MAX

# DLMM price maths requires very high precision
getcontext().prec = 50

# -------------------------
# Core DLMM price maths
# -------------------------


def price_from_bin_id(
    *,
    bin_id: int,
    bin_step_bps: int,
) -> Decimal:
    """
    DLMM price formula:
    price = (1 + bin_step / 10_000) ** bin_id
    """
    step = Decimal(bin_step_bps) / BASIS_POINT_MAX
    return (Decimal(1) + step) ** Decimal(bin_id)


def bin_id_from_price(
    *,
    price: Decimal,
    bin_step_bps: int,
    round_down: bool = True,
) -> int | None:
    """
    Inverse DLMM price formula.

    bin_id = log(price) / log(1 + bin_step)
    """
    if price <= 0:
        return None

    step = Decimal(bin_step_bps) / BASIS_POINT_MAX
    base = Decimal(1) + step

    raw = price.ln() / base.ln()

    if round_down:
        return int(raw.to_integral_value(rounding=ROUND_FLOOR))
    return int(raw.to_integral_value(rounding=ROUND_CEILING))


def to_price_per_lamport(
    *,
    price: Decimal,
    base_decimals: int,
    quote_decimals: int,
) -> Decimal:
    """
    Convert human price (tokenY / tokenX) to price per lamport.
    Equivalent to TS getPricePerLamport.
    """
    scale = Decimal(10) ** (base_decimals - quote_decimals)
    return price * scale


def from_price_per_lamport(
    *,
    price_per_lamport: Decimal,
    base_decimals: int,
    quote_decimals: int,
) -> Decimal:
    """
    Convert price per lamport back to human price (tokenY / tokenX).
    Inverse of price_per_lamport_from_price.
    """
    scale = Decimal(10) ** (quote_decimals - base_decimals)
    return price_per_lamport / scale


# -------------------------
# Helpers
# -------------------------


def price_range_for_bin(
    *,
    bin_id: int,
    active_id: int,
    bin_step: Decimal,
    base_price: Decimal = Decimal(1),
) -> tuple[Decimal, Decimal]:
    """
    Return (min_price, max_price) for a bin.
    """
    min_price = price_from_bin_id(
        bin_id=bin_id,
        bin_step_bps=bin_step,
    )

    max_price = price_from_bin_id(
        bin_id=bin_id + 1,
        bin_step_bps=bin_step,
    )

    return min_price, max_price


def bin_price_to_decimal(
    raw_price: int,
    base_decimals: int,
    quote_decimals: int,
) -> Decimal:
    """
    Converts bin.price (u128 Q64.64) into human price per token.
    """
    price = Decimal(raw_price) / Q64
    scale = Decimal(10) ** (base_decimals - quote_decimals)
    return price * scale
