from __future__ import annotations

from pathlib import Path

from PyQt5.QtWidgets import QFileDialog, QWidget

from utils.io import load_yaml, save_yaml


def choose_yaml_to_open(parent: QWidget) -> str | None:
    filename, _ = QFileDialog.getOpenFileName(parent, "Load YAML config", str(Path.cwd()), "YAML Files (*.yaml *.yml)")
    return filename or None


def choose_yaml_to_save(parent: QWidget) -> str | None:
    filename, _ = QFileDialog.getSaveFileName(parent, "Save YAML config", str(Path.cwd() / "saved_config.yaml"), "YAML Files (*.yaml *.yml)")
    return filename or None


def load_config_dialog(parent: QWidget) -> dict | None:
    path = choose_yaml_to_open(parent)
    if not path:
        return None
    return load_yaml(path)


def save_config_dialog(parent: QWidget, config: dict) -> str | None:
    path = choose_yaml_to_save(parent)
    if not path:
        return None
    save_yaml(config, path)
    return path
