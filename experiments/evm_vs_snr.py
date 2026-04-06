from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pandas as pd

from experiments.common import simulate_link
from utils.io import save_dataframe_csv, save_markdown_report
from utils.plotting import plot_metric_curve


def run_experiment(config: dict, output_dir: str | Path) -> pd.DataFrame:
    output_dir = Path(output_dir) / "evm_vs_snr"
    snr_values = config.get("experiments", {}).get("snr_sweep_db", list(range(0, 21, 2)))
    trials = int(config.get("experiments", {}).get("trials_per_point", 6))
    records = []

    for snr in snr_values:
        evm_values = []
        for _ in range(trials):
            trial_cfg = deepcopy(config)
            trial_cfg["channel"]["snr_db"] = float(snr)
            result = simulate_link(trial_cfg)
            evm_values.append(result["kpis"].evm)
        records.append({"snr_db": snr, "evm": sum(evm_values) / len(evm_values)})

    dataframe = pd.DataFrame(records)
    save_dataframe_csv(records, output_dir / "evm_vs_snr.csv")
    plot_metric_curve(dataframe, x="snr_db", y="evm", title="EVM vs SNR", output_path=output_dir / "evm_vs_snr.png")
    save_markdown_report(
        "EVM vs SNR",
        [("Summary", "```\n" + dataframe.to_string(index=False) + "\n```")],
        output_dir / "summary.md",
    )
    return dataframe
