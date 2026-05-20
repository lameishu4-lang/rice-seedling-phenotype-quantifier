# -*- coding: utf-8 -*-

from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def data_dir() -> Path:
    path = project_root() / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path


def output_dir() -> Path:
    path = project_root() / "outputs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def image_output_dir() -> Path:
    path = output_dir() / "images"
    path.mkdir(parents=True, exist_ok=True)
    return path


def report_output_dir() -> Path:
    path = output_dir() / "reports"
    path.mkdir(parents=True, exist_ok=True)
    return path


def database_path() -> Path:
    return data_dir() / "rice_phenotype.db"