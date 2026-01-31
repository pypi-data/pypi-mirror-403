from typing import Generator
from pathlib import Path

import polars as pl

from .client import anonymous_client


def load_blind_test(path: str, id: str, dissolve: bool = True):
    path = Path(path)
    if path.exists() and not path.is_dir():
        raise ValueError(f"Path {path} is not a directory")
    path.mkdir(parents=True, exist_ok=True)

    for file_name, df in get_blind_test(id):
        if dissolve:
            if 'gauge_id' in df.columns:
                for gauge_id, group in df.group_by('gauge_id'):
                    if isinstance(gauge_id, tuple):
                        gauge_id = gauge_id[0]
                    group.write_csv(path / f"{file_name}_{gauge_id}.csv")
            else:
                df.write_csv(path / f"{file_name}.csv")


def list_datasets():
    records = anonymous_client.collection("benchmark_dataset").get_full_list(
        query_params={"expand": "blind_data_via_dataset",}
    )

    return [record for record in records if 'blind_data_via_dataset' in record.expand]


def get_blind_test(id: str) -> Generator[tuple[str, pl.DataFrame], None, None]:
    record = anonymous_client.collection("blind_data").get_one(id)
    if record is None:
        raise ValueError(f"Blind test with id {id} not found")
    
    for file_name in record.files:
        file_url = anonymous_client.files.get_url(record, file_name)  
        df = pl.read_csv(file_url)
        yield (file_name, df)
