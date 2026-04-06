from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pandas as pd

from experiments.common import simulate_link
from utils.io import save_dataframe_csv, save_markdown_report
from utils.plotting import plot_metric_curve


def run_experiment(config: dict, output_dir: str | Path) -> pd.DataFrame:
    output_dir = Path(output_dir) / "control_vs_data"
    snr_values = config.get("experiments", {}).get("snr_sweep_db", [0, 4, 8, 12, 16, 20])
    records = []
    for snr in snr_values:
        for channel_type in ("control", "data"):
            trial_cfg = deepcopy(config)
            trial_cfg["channel"]["snr_db"] = float(snr)
            result = simulate_link(trial_cfg, channel_type=channel_type)
            row = result["kpis"].as_dict()
            row["snr_db"] = snr
            row["channel_type"] = channel_type
            records.append(row)

    dataframe = pd.DataFrame(records)
    save_dataframe_csv(records, output_dir / "control_vs_data.csv")
    pivot = dataframe.pivot(index="snr_db", columns="channel_type", values="bler").reset_index()
    plot_metric_curve(
        pivot.rename(columns={"control": "bler"}),
        x="snr_db",
        y="bler",
        title="Control BLER vs SNR",
        output_path=output_dir / "control_bler_vs_snr.png",
    )
    save_markdown_report(
        "Control vs Data",
        [("Summary", "```\n" + dataframe.to_string(index=False) + "\n```")],
        output_dir / "summary.md",
    )
    return dataframe
