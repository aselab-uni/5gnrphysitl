from __future__ import annotations

import os
from copy import deepcopy
from pathlib import Path

from experiments.common import simulate_link_sequence
from utils.io import load_yaml
from utils.validators import validate_config


def _uplink_control_config() -> dict:
    root = Path(__file__).resolve().parents[1]
    config = validate_config(load_yaml(root / "configs" / "default.yaml"))
    config = deepcopy(config)
    config["link"]["direction"] = "uplink"
    config["link"]["channel_type"] = "control"
    config["uplink"]["transform_precoding"] = False
    config["channel"]["model"] = "awgn"
    config["channel"]["snr_db"] = 28.0
    config["receiver"]["perfect_sync"] = True
    config["receiver"]["perfect_channel_estimation"] = True
    config["simulation"]["capture_slots"] = 2
    return config


def test_simulate_uplink_control_sequence() -> None:
    result = simulate_link_sequence(_uplink_control_config())

    assert result["captured_slots"] == 2
    assert result["tx"].metadata.direction == "uplink"
    assert result["tx"].metadata.channel_type == "control"
    assert result["tx"].metadata.transform_precoding_enabled is False
    assert result["tx"].metadata.payload_bits.size == result["config"]["control_channel"]["payload_bits"]
    assert result["rx"].crc_ok is True
    stage_names = [stage["stage"] for stage in result["pipeline"]]
    assert "Transform precoding" not in stage_names
    assert "Inverse transform precoding" not in stage_names


def test_phy_pipeline_panel_shows_uplink_control_without_transform_stages() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    try:
        from PyQt5.QtWidgets import QApplication
    except ImportError:  # pragma: no cover
        return

    from gui.phy_pipeline import PhyPipelinePanel

    app = QApplication.instance() or QApplication([])
    panel = PhyPipelinePanel()
    result = simulate_link_sequence(_uplink_control_config())
    panel.set_result(result)

    stage_keys = {stage["key"] for stage in panel.stages}
    assert "transform_precoding" not in stage_keys
    assert "inverse_transform_precoding" not in stage_keys
    panel.deleteLater()
    app.processEvents()
