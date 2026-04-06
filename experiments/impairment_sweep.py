from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pandas as pd

from experiments.common import simulate_link
from utils.io import save_dataframe_csv, save_markdown_report
from utils.plotting import plot_metric_curve


def run_experiment(config: dict, output_dir: str | Path) -> pd.DataFrame:
    output_dir = Path(output_dir) / "impairment_sweep"
    cfo_values = config.get("experiments", {}).get("cfo_sweep_hz", [0, 10, 30, 60, 120, 240])
    records = []
    for cfo_hz in cfo_values:
        trial_cfg = deepcopy(config)
        trial_cfg["channel"]["cfo_hz"] = float(cfo_hz)
        result = simulate_link(trial_cfg)
        row = result["kpis"].as_dict()
        row["cfo_hz"] = cfo_hz
        records.append(row)

    dataframe = pd.DataFrame(records)
    save_dataframe_csv(records, output_dir / "impairment_sweep.csv")
    plot_metric_curve(
        dataframe,
        x="cfo_hz",
        y="ber",
        title="BER vs CFO",
        output_path=output_dir / "ber_vs_cfo.png",
    )
    save_markdown_report(
        "Impairment Sweep",
        [("Summary", "```\n" + dataframe.to_string(index=False) + "\n```")],
        output_dir / "summary.md",
    )
    return dataframe
