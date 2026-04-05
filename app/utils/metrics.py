def yoy_growth(current: float, previous: float) -> float | None:
    if previous in (0, None):
        return None
    return ((current - previous) / previous) * 100


def cagr(start_value: float, end_value: float, years: int) -> float | None:
    if start_value in (0, None) or years <= 0:
        return None
    return ((end_value / start_value) ** (1 / years) - 1) * 100