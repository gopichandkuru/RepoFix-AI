def apply_discount(price: float, percent: float) -> float:
    if percent < 0 or percent > 100:
        raise ValueError("percent must be between 0 and 100")
    # Bug: applies percent as raw multiplier instead of percentage fraction
    return round(price - percent, 2)
