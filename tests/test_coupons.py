"""Fit-coupon validity and official-derived interface checks."""

from __future__ import annotations

import pytest

from satellite1_ultra.coupons import COUPONS


@pytest.mark.geometry
@pytest.mark.parametrize("name", sorted(COUPONS))
def test_coupon_is_a_valid_single_solid(name: str) -> None:
    shape = COUPONS[name]()
    box = shape.BoundingBox()
    assert shape.isValid()
    assert len(shape.Solids()) == 1
    assert shape.Volume() > 100.0
    assert max(box.xlen, box.ylen, box.zlen) <= 256.0
