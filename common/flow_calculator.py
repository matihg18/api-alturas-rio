from typing import Optional


def compute_flow(h: float, a: float, b: float, h0: float) -> Optional[float]:
    effective_h = h - h0
    if effective_h <= 0:
        return None
    return a * (effective_h ** b)
