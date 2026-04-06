from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path
from typing import Dict, List

import pandas as pd

from experiments.common import simulate_link
from utils.io import load_yaml, save_dataframe_csv, save_markdown_report
from utils.validators import deep_merge, validate_config


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run advanced 3GPP-inspired 5G NR PHY showcases.")
    parser.add_argument("--config", type=str, default="configs/default.yaml")
    parser.add_argument("--override", type=str, nargs="*", default=[])
    parser.add_argument("--output-dir", type=str, default="outputs/showcases")
    return parser


def load_config(base_path: str, overrides: List[str]) -> dict:
    project_root = Path(__file__).resolve().parent
    config = load_yaml(project_root / base_path)
    for override in overrides:
        config = deep_merge(config, load_yaml(project_root / override))
    return validate_config(config)


def summarize_result(showcase_id: str, concept: str, scenario: str, result: Dict, extra: Dict | None = None) -> Dict:
    row = {
        "showcase_id": showcase_id,
        "concept": concept,
        "scenario": scenario,
    }
    row.update(result["kpis"].as_dict())
    if extra:
        row.update(extra)
    return row


def run_showcases(base_config: dict) -> pd.DataFrame:
    rows: List[Dict] = []

    # SC1: Link adaptation intuition across cell-center vs cell-edge.
    mcs_like_profiles = [
        ("QPSK", 0.50),
        ("16QAM", 0.50),
        ("64QAM", 0.70),
        ("256QAM", 0.80),
    ]
    for zone, snr_db in [("cell_center", 20), ("cell_edge", 0)]:
        for modulation, target_rate in mcs_like_profiles:
            config = deepcopy(base_config)
            config["channel"]["snr_db"] = snr_db
            config["modulation"]["scheme"] = modulation
            config["coding"]["target_rate"] = target_rate
            result = simulate_link(config, channel_type="data")
            rows.append(
                summarize_result(
                    "SC1",
                    "Link adaptation maps channel quality to modulation and coding choices.",
                    f"{zone}_{modulation}_r{target_rate:.2f}",
                    result,
                    {
                        "zone": zone,
                        "snr_db": snr_db,
                        "modulation": modulation,
                        "target_rate": target_rate,
                    },
                )
            )

    # SC2: 256QAM sensitivity to SNR.
    for snr_db in [0, 5, 10, 15, 20]:
        config = deepcopy(base_config)
        config["channel"]["snr_db"] = snr_db
        config["modulation"]["scheme"] = "256QAM"
        config["coding"]["target_rate"] = 0.80
        result = simulate_link(config, channel_type="data")
        rows.append(
            summarize_result(
                "SC2",
                "High-order QAM increases spectral efficiency at the cost of SNR sensitivity.",
                f"256QAM_snr{snr_db}",
                result,
                {"snr_db": snr_db, "modulation": "256QAM", "target_rate": 0.80},
            )
        )

    # SC3: DMRS-based channel estimation vs perfect channel knowledge.
    for profile, model in [("pedestrian", "rayleigh"), ("vehicular", "rayleigh"), ("urban_los", "rician")]:
        for perfect_ce in [True, False]:
            config = deepcopy(base_config)
            config["channel"]["model"] = model
            config["channel"]["fading_type"] = model
            config["channel"]["profile"] = profile
            config["channel"]["snr_db"] = 15
            config["receiver"]["perfect_channel_estimation"] = perfect_ce
            result = simulate_link(config, channel_type="data")
            rows.append(
                summarize_result(
                    "SC3",
                    "DMRS and channel estimation quality strongly influence equalization and EVM in fading channels.",
                    f"{profile}_{'perfectCE' if perfect_ce else 'dmrsLS'}",
                    result,
                    {
                        "profile": profile,
                        "channel_model": model,
                        "perfect_channel_estimation": float(perfect_ce),
                        "snr_db": 15,
                    },
                )
            )

    # SC4: Numerology intuition under mobility.
    numerologies = [
        ("mu0_15k", 15, 256, 18, 12),
        ("mu1_30k", 30, 512, 36, 24),
        ("mu2_60k", 60, 1024, 72, 48),
    ]
    for name, scs_khz, fft_size, cp_length, n_rb in numerologies:
        config = deepcopy(base_config)
        config["numerology"].update(
            {
                "scs_khz": scs_khz,
                "fft_size": fft_size,
                "cp_length": cp_length,
                "n_rb": n_rb,
            }
        )
        config["carrier"]["bandwidth_hz"] = n_rb * 12 * scs_khz * 1e3
        config["channel"].update(
            {
                "model": "rayleigh",
                "profile": "vehicular",
                "fading_type": "rayleigh",
                "doppler_hz": 200,
                "snr_db": 15,
            }
        )
        config["receiver"]["perfect_channel_estimation"] = False
        result = simulate_link(config, channel_type="data")
        rows.append(
            summarize_result(
                "SC4",
                "NR numerology changes OFDM symbol duration and affects Doppler robustness.",
                name,
                result,
                {
                    "scs_khz": scs_khz,
                    "fft_size": fft_size,
                    "cp_length": cp_length,
                    "n_rb": n_rb,
                    "doppler_hz": 200,
                    "snr_db": 15,
                },
            )
        )

    # SC5: Baseline vs harsh vehicular stress.
    for scenario_name, params in [
        (
            "baseline_awgn",
            {
                "modulation": "QPSK",
                "target_rate": 0.50,
                "channel": {"model": "awgn", "profile": "static_near", "snr_db": 40},
            },
        ),
        (
            "vehicular_stress",
            {
                "modulation": "16QAM",
                "target_rate": 0.55,
                "channel": {
                    "model": "rayleigh",
                    "profile": "vehicular",
                    "fading_type": "rayleigh",
                    "snr_db": 14,
                    "doppler_hz": 140,
                    "delay_spread_s": 1.76e-6,
                    "cfo_hz": 45,
                    "sto_samples": 6,
                },
            },
        ),
    ]:
        config = deepcopy(base_config)
        config["modulation"]["scheme"] = params["modulation"]
        config["coding"]["target_rate"] = params["target_rate"]
        config["channel"].update(params["channel"])
        result = simulate_link(config, channel_type="data")
        rows.append(
            summarize_result(
                "SC5",
                "Real deployments must survive a wide gap between lab-clean and mobility-stressed channels.",
                scenario_name,
                result,
                {
                    "modulation": params["modulation"],
                    "target_rate": params["target_rate"],
                    "profile": params["channel"].get("profile"),
                    "snr_db": params["channel"].get("snr_db"),
                    "doppler_hz": params["channel"].get("doppler_hz"),
                    "cfo_hz": params["channel"].get("cfo_hz"),
                    "sto_samples": params["channel"].get("sto_samples"),
                },
            )
        )

    return pd.DataFrame(rows)


def build_markdown_sections(dataframe: pd.DataFrame) -> List[tuple[str, str]]:
    sections: List[tuple[str, str]] = []
    for showcase_id, showcase_rows in dataframe.groupby("showcase_id", sort=False):
        concept = showcase_rows["concept"].iloc[0]
        table = "```\n" + showcase_rows.drop(columns=["concept"]).to_string(index=False) + "\n```"
        sections.append((f"{showcase_id} - {concept}", table))
    return sections


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()
    project_root = Path(__file__).resolve().parent
    config = load_config(args.config, args.override)
    dataframe = run_showcases(config)

    output_dir = project_root / args.output_dir
    save_dataframe_csv(dataframe.to_dict(orient="records"), output_dir / "showcases.csv")
    save_markdown_report("3GPP-Inspired PHY Showcases", build_markdown_sections(dataframe), output_dir / "showcases.md")
    print(dataframe.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
