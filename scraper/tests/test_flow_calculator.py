import pytest
from common.flow_calculator import compute_flow

EL_SOBERBIO    = dict(a=643.10, b=1.331, h0=-0.005)
SAN_JAVIER     = dict(a=500.39, b=1.639, h0=-0.005)
GARRUCHOS      = dict(a=70.07,  b=1.978, h0=-3.228)
SANTO_TOME     = dict(a=39.11,  b=2.246, h0=-2.469)
ALVEAR         = dict(a=0.212,  b=3.964, h0=-6.786)
PASO_LOS_LIBRES = dict(a=218.51, b=1.840, h0=-1.307)



class TestComputeFlowInvalidRange:

    def test_h_equals_h0_returns_none(self):
        p = EL_SOBERBIO
        assert compute_flow(h=p["h0"], **p) is None

    def test_h_below_h0_returns_none(self):
        p = GARRUCHOS
        assert compute_flow(h=-3.5, **p) is None

    def test_h_slightly_below_h0_returns_none(self):
        p = ALVEAR
        assert compute_flow(h=-6.787, **p) is None

    def test_h_equal_h0_for_all_stations(self):
        for params in [EL_SOBERBIO, SAN_JAVIER, GARRUCHOS, SANTO_TOME, ALVEAR, PASO_LOS_LIBRES]:
            assert compute_flow(h=params["h0"], **params) is None, (
                f"Esperaba None para H=H₀={params['h0']}"
            )

class TestComputeFlowValidResults:

    def test_el_soberbio_returns_positive(self):
        result = compute_flow(h=5.0, **EL_SOBERBIO)
        assert result is not None
        assert result > 0

    def test_el_soberbio_formula(self):
        h = 5.0
        p = EL_SOBERBIO
        expected = p["a"] * ((h - p["h0"]) ** p["b"])
        result = compute_flow(h=h, **p)
        assert result == pytest.approx(expected, rel=1e-9)

    def test_garruchos_formula(self):
        h = 10.0
        p = GARRUCHOS
        expected = p["a"] * ((h - p["h0"]) ** p["b"])
        result = compute_flow(h=h, **p)
        assert result == pytest.approx(expected, rel=1e-9)

    def test_alvear_formula(self):
        h = 0.0
        p = ALVEAR
        expected = p["a"] * ((h - p["h0"]) ** p["b"])
        result = compute_flow(h=h, **p)
        assert result == pytest.approx(expected, rel=1e-9)

    def test_all_stations_return_positive_for_typical_levels(self):
        typical_h = 5.0
        for params in [EL_SOBERBIO, SAN_JAVIER, GARRUCHOS, SANTO_TOME, ALVEAR, PASO_LOS_LIBRES]:
            result = compute_flow(h=typical_h, **params)
            assert result is not None and result > 0, (
                f"Esperaba Q > 0 para H={typical_h} con params={params}"
            )

    def test_higher_h_gives_higher_flow(self):
        p = EL_SOBERBIO
        q_low  = compute_flow(h=3.0, **p)
        q_high = compute_flow(h=8.0, **p)
        assert q_low is not None
        assert q_high is not None
        assert q_high > q_low
