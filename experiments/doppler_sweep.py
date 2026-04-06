from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pandas as pd

from experiments.common import simulate_link
from utils.io import save_dataframe_csv, save_markdown_report
from utils.plotting import plot_metric_curve


def run_experiment(config: dict, output_dir: str | Path) -> pd.DataFrame:
    output_dir = Path(output_dir) / "doppler_sweep"
    doppler_values = config.get("experiments", {}).get("doppler_sweep_hz", [0, 5, 25, 50, 100, 200])
    records = []
    for doppler_hz in doppler_values:
        trial_cfg = deepcopy(config)
        trial_cfg["channel"]["doppler_hz"] = float(doppler_hz)
        result = simulate_link(trial_cfg)
        row = result["kpis"].as_dict()
        row["doppler_hz"] = doppler_hz
        records.append(row)

    dataframe = pd.DataFrame(records)
    save_dataframe_csv(records, output_dir / "doppler_sweep.csv")
    plot_metric_curve(
        dataframe,
        x="doppler_hz",
        y="ber",
        title="BER vs Doppler",
        output_path=output_dir / "ber_vs_doppler.png",
    )
    save_markdown_report(
        "Doppler Sweep",
        [("Summary", "```\n" + dataframe.to_string(index=False) + "\n```")],
        output_dir / "summary.md",
    )
    return dataframe
