from __future__ import annotations

import os
from copy import deepcopy
from pathlib import Path

from experiments.common import simulate_link_sequence
from utils.io import load_yaml
from utils.validators import validate_config


def _prach_config() -> dict:
    root = Path(__file__).resolve().parents[1]
    config = validate_config(load_yaml(root / "configs" / "default.yaml"))
    config = deepcopy(config)
    config["link"]["direction"] = "uplink"
    config["link"]["channel_type"] = "prach"
    config["simulation"]["capture_slots"] = 2
    config["channel"]["model"] = "awgn"
    config["channel"]["snr_db"] = 24.0
    config["receiver"]["perfect_sync"] = True
    config["receiver"]["perfect_channel_estimation"] = True
    return config


def test_simulate_uplink_prach_sequence() -> None:
    result = simulate_link_sequence(_prach_config())

    assert result["captured_slots"] == 2
    assert result["tx"].metadata.direction == "uplink"
    assert result["tx"].metadata.channel_type == "prach"
    assert result["tx"].metadata.prach_sequence is not None
    assert result["rx"].detected_preamble_id == result["tx"].metadata.prach_preamble_id
    assert result["rx"].crc_ok is True

    stage_names = [stage["stage"] for stage in result["pipeline"]]
    assert "PRACH preamble generation" in stage_names
    assert "PRACH correlation detector" in stage_names


def test_phy_pipeline_panel_shows_prach_specific_stages() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    try:
        from PyQt5.QtWidgets import QApplication
    except ImportError:  # pragma: no cover
        return

    from gui.phy_pipeline import PhyPipelinePanel

    app = QApplication.instance() or QApplication([])
    panel = PhyPipelinePanel()
    result = simulate_link_sequence(_prach_config())
    panel.set_result(result)

    stage_titles = {str(stage["title"]).lower() for stage in panel.stages}
    assert "prach preamble generation" in stage_titles
    assert "prach correlation detector" in stage_titles
    panel.deleteLater()
    app.processEvents()
