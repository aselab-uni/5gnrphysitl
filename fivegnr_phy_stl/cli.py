from __future__ import annotations

import argparse
import json
from pathlib import Path

from experiments.common import simulate_link
from gui.app import launch_app
from run_experiments import EXPERIMENTS
from run_showcases import build_markdown_sections as build_showcase_sections
from run_showcases import run_showcases
from run_student_testcases import AVAILABLE_CASE_IDS, build_markdown_sections as build_student_sections
from run_student_testcases import run_cases
from utils.io import load_yaml, save_dataframe_csv, save_markdown_report
from utils.logging_utils import configure_logging
from utils.validators import deep_merge, validate_config

from ._config import resolve_config_path


def _load_config(base_path: str, overrides: list[str]) -> dict:
    config = load_yaml(resolve_config_path(base_path))
    for override in overrides:
        config = deep_merge(config, load_yaml(resolve_config_path(override)))
    return validate_config(config)


def _single_link_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="5G NR PHY STL package entry point")
    parser.add_argument("--config", type=str, default="configs/default.yaml")
    parser.add_argument("--override", type=str, nargs="*", default=[])
    parser.add_argument("--gui", action="store_true")
    parser.add_argument("--channel-type", type=str, default=None, choices=["data", "control"])
    parser.add_argument("--log-level", type=str, default="INFO")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _single_link_arg_parser()
    args = parser.parse_args(argv)
    logger = configure_logging(log_level=args.log_level)
    config = _load_config(args.config, args.override)
    if args.gui:
        logger.info("Launching 5G NR PHY STL GUI.")
        launch_app(config)
        return 0
    result = simulate_link(config=config, channel_type=args.channel_type)
    logger.info("Simulation completed.")
    print(json.dumps(result["kpis"].as_dict(), indent=2))
    return 0


def gui_main(argv: list[str] | None = None) -> int:
    parser = _single_link_arg_parser()
    args = parser.parse_args(argv)
    config = _load_config(args.config, args.override)
    launch_app(config)
    return 0


def experiments_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run batch experiments for the 5G NR PHY STL package.")
    parser.add_argument("--experiment", type=str, required=True, choices=sorted(EXPERIMENTS.keys()))
    parser.add_argument("--config", type=str, default="configs/default.yaml")
    parser.add_argument("--override", type=str, nargs="*", default=[])
    parser.add_argument("--output-dir", type=str, default="outputs")
    args = parser.parse_args(argv)

    config = _load_config(args.config, args.override)
    runner = EXPERIMENTS[args.experiment]
    runner(config=config, output_dir=Path(args.output_dir))
    return 0


def student_cases_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run curated teaching-oriented 5G NR PHY testcases.")
    parser.add_argument("--config", type=str, default="configs/default.yaml")
    parser.add_argument("--override", type=str, nargs="*", default=[])
    parser.add_argument("--output-dir", type=str, default="outputs/student_testcases")
    parser.add_argument("--case-id", action="append", choices=AVAILABLE_CASE_IDS, default=[])
    parser.add_argument("--list-cases", action="store_true")
    args = parser.parse_args(argv)

    if args.list_cases:
        for case_id in AVAILABLE_CASE_IDS:
            print(case_id)
        return 0

    config = _load_config(args.config, args.override)
    selected_case_ids = set(args.case_id) if args.case_id else set(AVAILABLE_CASE_IDS)
    dataframe = run_cases(config, selected_case_ids=selected_case_ids)
    output_dir = Path(args.output_dir)
    save_dataframe_csv(dataframe.to_dict(orient="records"), output_dir / "student_testcases.csv")
    save_markdown_report("Student Testcases", build_student_sections(dataframe), output_dir / "student_testcases.md")
    print(dataframe.to_string(index=False))
    return 0


def showcases_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run advanced 3GPP-inspired 5G NR PHY showcases.")
    parser.add_argument("--config", type=str, default="configs/default.yaml")
    parser.add_argument("--override", type=str, nargs="*", default=[])
    parser.add_argument("--output-dir", type=str, default="outputs/showcases")
    args = parser.parse_args(argv)

    config = _load_config(args.config, args.override)
    dataframe = run_showcases(config)
    output_dir = Path(args.output_dir)
    save_dataframe_csv(dataframe.to_dict(orient="records"), output_dir / "showcases.csv")
    save_markdown_report("3GPP-Inspired PHY Showcases", build_showcase_sections(dataframe), output_dir / "showcases.md")
    print(dataframe.to_string(index=False))
    return 0
