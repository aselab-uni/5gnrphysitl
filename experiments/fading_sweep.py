from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pandas as pd

from experiments.common import simulate_link
from utils.io import save_dataframe_csv, save_markdown_report


def run_experiment(config: dict, output_dir: str | Path) -> pd.DataFrame:
    output_dir = Path(output_dir) / "fading_sweep"
    profiles = ["static_near", "cell_edge", "pedestrian", "vehicular", "urban_los", "urban_nlos", "severe_fading"]
    records = []
    for profile in profiles:
        trial_cfg = deepcopy(config)
        trial_cfg["channel"]["profile"] = profile
        trial_cfg["channel"]["model"] = "rician" if "los" in profile else "rayleigh"
        trial_cfg["channel"]["fading_type"] = trial_cfg["channel"]["model"]
        result = simulate_link(trial_cfg)
        row = result["kpis"].as_dict()
        row["profile"] = profile
        records.append(row)

    dataframe = pd.DataFrame(records)
    save_dataframe_csv(records, output_dir / "fading_sweep.csv")
    save_markdown_report(
        "Fading Sweep",
        [("Summary", "```\n" + dataframe.to_string(index=False) + "\n```")],
        output_dir / "summary.md",
    )
    return dataframe
