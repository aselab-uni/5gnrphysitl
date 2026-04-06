from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pandas as pd

from experiments.common import simulate_link
from utils.io import save_dataframe_csv, save_markdown_report
from utils.plotting import plot_metric_curve


def run_experiment(config: dict, output_dir: str | Path) -> pd.DataFrame:
    output_dir = Path(output_dir) / "bler_vs_snr"
    snr_values = config.get("experiments", {}).get("snr_sweep_db", list(range(0, 21, 2)))
    trials = int(config.get("experiments", {}).get("trials_per_point", 8))
    records = []

    for snr in snr_values:
        bler_values = []
        throughput_values = []
        for _ in range(trials):
            trial_cfg = deepcopy(config)
            trial_cfg["channel"]["snr_db"] = float(snr)
            result = simulate_link(trial_cfg)
            bler_values.append(result["kpis"].bler)
            throughput_values.append(result["kpis"].throughput_bps)
        records.append(
            {
                "snr_db": snr,
                "bler": sum(bler_values) / len(bler_values),
                "throughput_bps": sum(throughput_values) / len(throughput_values),
            }
        )

    dataframe = pd.DataFrame(records)
    save_dataframe_csv(records, output_dir / "bler_vs_snr.csv")
    plot_metric_curve(dataframe, x="snr_db", y="bler", title="BLER vs SNR", output_path=output_dir / "bler_vs_snr.png")
    save_markdown_report(
        "BLER vs SNR",
        [("Summary", "```\n" + dataframe.to_string(index=False) + "\n```")],
        output_dir / "summary.md",
    )
    return dataframe
