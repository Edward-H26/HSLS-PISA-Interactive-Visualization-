from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, MutableMapping, Any

import configparser
import json
import numpy as np
import pandas as pd

DATASET_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "dataset.ini"
PROCESS_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "data_process.ini"


def _load_ini_config(path: Path) -> configparser.ConfigParser:
    parser = configparser.ConfigParser(interpolation = None)
    parser.optionxform = str
    parser.read(path, encoding = "utf-8")
    return parser


def _extract_section_config(
    parser: configparser.ConfigParser,
    section: str,
) -> tuple[str, MutableMapping[str, str]]:
    section_data = parser[section]
    dataset_path = section_data["dataset_path"]
    fields: MutableMapping[str, str] = {
        key: value for key, value in section_data.items() if key != "dataset_path"
    }
    return dataset_path, fields


def _parse_list(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_value_map(value: str) -> Dict[int, str]:
    value = value.strip()
    if not value:
        return {}

    if value.startswith("{") and value.endswith("}"):
        parsed = json.loads(value)
        return {int(k): str(v) for k, v in parsed.items()}

    mapping: Dict[int, str] = {}
    for pair in value.split(","):
        if ":" not in pair:
            continue
        raw_key, raw_val = pair.split(":", 1)
        key = int(raw_key.strip())
        mapping[key] = raw_val.strip()
    return mapping


def _load_missing_codes(parser: configparser.ConfigParser) -> List[int]:
    if "missing_codes" not in parser or "codes" not in parser["missing_codes"]:
        return []
    return [int(item) for item in _parse_list(parser["missing_codes"]["codes"])]


def _load_mappings(parser: configparser.ConfigParser) -> List[Dict[str, Any]]:
    mappings: List[Dict[str, Any]] = []
    for section in parser.sections():
        if not section.startswith("mapping."):
            continue
        cfg = parser[section]
        if cfg.get("type", "map").lower() != "map":
            continue
        sources = _parse_list(cfg.get("source", ""))
        targets = _parse_list(cfg.get("target", ""))
        if not sources:
            continue
        if targets and len(targets) != len(sources):
            continue
        if not targets:
            targets = sources
        raw_map = _parse_value_map(cfg.get("map_json") or cfg.get("map", ""))
        mappings.append({"sources": sources, "targets": targets, "map": raw_map})
    return mappings


_DATASET_CONFIG = _load_ini_config(DATASET_CONFIG_PATH)


def load_process_config(config: str | Path | configparser.ConfigParser) -> configparser.ConfigParser:
    if isinstance(config, configparser.ConfigParser):
        return config
    return _load_ini_config(Path(config))


def get_available_datasets() -> List[str]:
    return _DATASET_CONFIG.sections()


def load_configured_fields(
    field_names: Iterable[str] = None,
    dataset_name: str = None,
    dataset_path: str | Path = None,
) -> pd.DataFrame:
    base_fields: MutableMapping[str, str] = {}
    resolved_path = dataset_path

    if dataset_name:
        section_path, section_fields = _extract_section_config(_DATASET_CONFIG, dataset_name)
        resolved_path = resolved_path or section_path
        base_fields = section_fields

    requested = list(dict.fromkeys(field_names or base_fields.keys()))

    if not requested:
        return pd.DataFrame()

    resolved_path = Path(resolved_path) if isinstance(resolved_path, Path) else resolved_path
    available_columns = pd.read_csv(resolved_path, nrows = 0).columns.tolist()

    selected = [col for col in requested if col in available_columns]

    if not selected:
        return pd.DataFrame(columns = requested)

    return pd.read_csv(resolved_path, usecols = selected, low_memory = False)


def process_data(df: pd.DataFrame, process_config: str | Path | configparser.ConfigParser) -> pd.DataFrame:
    parser = load_process_config(process_config)

    missing_codes = _load_missing_codes(parser)
    mappings = _load_mappings(parser)

    df_processed = df.copy()
    if missing_codes:
        df_processed = df_processed.replace(missing_codes, np.nan)

    for mapping in mappings:
        map_dict = mapping.get("map")
        for source, target in zip(mapping["sources"], mapping["targets"]):
            if source in df_processed.columns:
                df_processed[target] = (
                    df_processed[source].map(map_dict) if map_dict else df_processed[source]
                )

    return df_processed


class DataLoader:
    def __init__(self, dataset_name: str) -> None:
        self.dataset_name = dataset_name
        section_path, section_fields = _extract_section_config(_DATASET_CONFIG, self.dataset_name)

        self.dataset_path = section_path
        self.field_names = list(section_fields.keys())
        self.df: pd.DataFrame = pd.DataFrame()
        self.load_data()

    def load_data(self, field_names: Iterable[str] = None) -> pd.DataFrame:
        requested_fields = list(dict.fromkeys(field_names or self.field_names))
        self.field_names = requested_fields
        self.df = load_configured_fields(
            field_names = self.field_names,
            dataset_name = self.dataset_name,
            dataset_path = self.dataset_path,
        )
        return self.df
