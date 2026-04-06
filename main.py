from __future__ import annotations

import argparse
import json
from pathlib import Path

from experiments.common import simulate_link
from utils.io import load_yaml
from utils.logging_utils import configure_logging
from utils.validators import deep_merge, validate_config


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="5G NR PHY STL prototype")
    parser.add_argument("--config", type=str, default="configs/default.yaml", help="Base YAML configuration file.")
    parser.add_argument("--override", type=str, nargs="*", default=[], help="Additional YAML files merged on top of the base config.")
    parser.add_argument("--gui", action="store_true", help="Launch the Qt GUI dashboard.")
    parser.add_argument("--channel-type", type=str, default=None, choices=["data", "control"], help="Override data/control channel mode.")
    parser.add_argument("--log-level", type=str, default="INFO", help="Python logging level.")
    return parser


def load_config(base_path: str, overrides: list[str]) -> dict:
    project_root = Path(__file__).resolve().parent
    config = load_yaml(project_root / base_path)
    for override in overrides:
        config = deep_merge(config, load_yaml(project_root / override))
    return validate_config(config)


def launch_gui(config: dict) -> None:
    from gui.app import launch_app

    launch_app(config)


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()
    logger = configure_logging(log_level=args.log_level)
    config = load_config(args.config, args.override)

    if args.gui:
        logger.info("Launching 5G NR PHY STL GUI.")
        launch_gui(config)
        return 0

    result = simulate_link(config=config, channel_type=args.channel_type)
    logger.info("Simulation completed.")
    print(json.dumps(result["kpis"].as_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
