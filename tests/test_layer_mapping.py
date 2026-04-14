from __future__ import annotations

import os
from copy import deepcopy
from pathlib import Path

import numpy as np

from experiments.common import simulate_link
from phy.layer_mapping import combine_layer_symbols, layer_map_symbols
from utils.io import load_yaml
from utils.validators import validate_config


def _layer_config() -> dict:
    root = Path(__file__).resolve().parents[1]
    config = validate_config(load_yaml(root / "configs" / "default.yaml"))
    config = deepcopy(config)
    config["channel"]["model"] = "awgn"
    config["channel"]["snr_db"] = 40.0
    config["receiver"]["perfect_sync"] = True
    config["receiver"]["perfect_channel_estimation"] = True
    config["spatial"]["num_layers"] = 2
    config["spatial"]["num_ports"] = 2
    config["spatial"]["num_tx_antennas"] = 2
    config["spatial"]["num_rx_antennas"] = 2
    return config


def test_layer_map_symbols_round_trips_combined_order() -> None:
    symbols = np.asarray([1 + 0j, 2 + 0j, 3 + 0j, 4 + 0j, 5 + 0j, 6 + 0j], dtype=np.complex128)
    layer_symbols = layer_map_symbols(symbols, 2)

    assert layer_symbols.shape == (2, 3)
    np.testing.assert_allclose(layer_symbols[0], np.asarray([1 + 0j, 3 + 0j, 5 + 0j]))
    np.testing.assert_allclose(layer_symbols[1], np.asarray([2 + 0j, 4 + 0j, 6 + 0j]))
    np.testing.assert_allclose(combine_layer_symbols(layer_symbols, total_symbols=symbols.size), symbols)


def test_two_layer_baseline_runs_end_to_end() -> None:
    result = simulate_link(_layer_config())
    tx = result["tx"]
    rx = result["rx"]

    assert tx.waveform.ndim == 2
    assert tx.waveform.shape[0] == 2
    assert tx.metadata.tx_layer_symbols.shape[0] == 2
    assert tx.metadata.tx_layer_grid.shape[0] == 2
    assert tx.metadata.tx_port_grid.shape[0] == 2
    assert tx.metadata.mapping.bits_capacity == tx.metadata.mapping.positions.shape[0] * tx.metadata.mapper.bits_per_symbol * 2
    assert rx.rx_layer_symbols.shape[0] == 2
    assert rx.equalized_layer_symbols.shape[0] == 2
    assert rx.detected_layer_symbols.shape[0] == 2
    assert rx.re_data_positions.shape[0] == rx.re_data_symbols.shape[0]
    assert rx.detected_symbols.shape == tx.metadata.modulation_symbols.shape
    assert rx.crc_ok is True
    assert result["kpis"].ber == 0.0


def test_phy_pipeline_panel_shows_layer_mapping_artifacts() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    try:
        from PyQt5.QtWidgets import QApplication
    except ImportError:  # pragma: no cover
        return

    from gui.phy_pipeline import PhyPipelinePanel

    app = QApplication.instance() or QApplication([])
    panel = PhyPipelinePanel()
    panel.set_result(simulate_link(_layer_config()))

    stage = next(stage for stage in panel.stages if stage["key"] == "layer_mapping")
    artifact_names = [artifact["name"] for artifact in stage["artifacts"]]
    assert "Per-layer constellation" in artifact_names
    assert "Layer 0 occupancy" in artifact_names
    assert "Layer 1 occupancy" in artifact_names
    panel.deleteLater()
    app.processEvents()
