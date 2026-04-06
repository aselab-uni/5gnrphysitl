from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def plot_metric_curve(
    dataframe: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    output_path: str | Path,
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, axis = plt.subplots(figsize=(7, 4))
    axis.plot(dataframe[x], dataframe[y], marker="o")
    axis.set_title(title)
    axis.set_xlabel(x)
    axis.set_ylabel(y)
    axis.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path
