from importlib import resources
from pathlib import Path

import pandas as pd


def _data_dir() -> Path:
    return Path(resources.files("mls_2425_advanced_stats") / "data")


def list_datasets() -> list[str]:
    """Return sorted list of available dataset names (without .csv extension)."""
    return sorted(p.stem for p in _data_dir().glob("*.csv"))


def load(name: str) -> pd.DataFrame:
    """Load a dataset by name (e.g. '2024_standardStats') and return a DataFrame."""
    path = _data_dir() / f"{name}.csv"
    if not path.exists():
        raise ValueError(
            f"Dataset '{name}' not found. Available: {list_datasets()}"
        )
    return pd.read_csv(path)


def load_year(year: int) -> dict[str, pd.DataFrame]:
    """Load all datasets for a given year. Returns dict of name -> DataFrame."""
    prefix = str(year)
    return {
        name: load(name)
        for name in list_datasets()
        if name.startswith(prefix)
    }


def load_all() -> dict[str, pd.DataFrame]:
    """Load all datasets. Returns dict of name -> DataFrame."""
    return {name: load(name) for name in list_datasets()}
