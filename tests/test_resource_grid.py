from __future__ import annotations

from phy.frame_structure import build_default_allocation
from phy.numerology import NumerologyConfig
from phy.resource_grid import ResourceGrid


def test_resource_grid_positions_are_non_empty() -> None:
    numerology = NumerologyConfig(scs_khz=30, fft_size=512, cp_length=36, n_rb=24)
    config = {"frame": {"control_symbols": 2, "pdsch_start_symbol": 2, "dmrs_symbols": [3, 10]}}
    allocation = build_default_allocation(numerology, config)
    grid = ResourceGrid(numerology, allocation)
    assert grid.pdcch_positions().shape[0] > 0
    assert grid.pdsch_positions().shape[0] > 0
    assert grid.dmrs_positions().shape[0] > 0
