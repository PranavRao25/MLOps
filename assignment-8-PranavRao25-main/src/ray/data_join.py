import ray
import pandas as pd
import yaml
from pathlib import Path
import numpy as np
from ray.data_clean import process_data

parent = Path(__file__).resolve().parent.parent.parent
with open(parent / "config.yaml") as f:
    configs = yaml.full_load(f)

parent_path = parent / configs["data"]["raw"]
# production_path = parent / configs["data"]["production"]
features = configs["data"]["labels"]

system_configs = configs["ray"]["system"]
BATCH_SIZE = system_configs["batch_size"]
num_cpus = system_configs["num_cpus"]
concurrency = system_configs["concurrency"]

def broadcast_join(batch: pd.DataFrame, lookup: dict):
    lookup_df = pd.DataFrame(lookup.values())
    return batch.merge(lookup_df, on="id", how="left")

def derive_complex_features(batch: pd.DataFrame):
    # TODO: Domain specific computations
    return batch

if __name__ == "__main__":
    dashboard_system = configs["ray"]["dashboard"]
    master_system = configs["ray"]["master"]
    master_ip, master_port = master_system["ip"], master_system["port"]

    ray.init(address=f"ray://{master_ip}:4532")

    ds1 = ray.data.read_parquet("")
    ds2 = ray.data.read_parquet("")

    # ASSUME BROADCAST JOIN (TABLES SIZES < 2 GB)

    ds1_lookup = {
        row["id"]: row
        for row in ds1.to_pandas().to_dict(orient="records")
    }

    ds1_ref = ray.put(ds1_lookup)

    joined_ds = ds2.map_batches(
        lambda batch: broadcast_join(batch, ray.get(ds1_ref)), # type: ignore
        batch_size=BATCH_SIZE,
        batch_format="pandas",
        num_cpus=num_cpus,
        concurrency=concurrency
    )
    clean_joined_ds = process_data(joined_ds)

    final_ds = clean_joined_ds.map_batches(
        derive_complex_features, # type: ignore
        batch_size=BATCH_SIZE,
        batch_format="pandas",
        num_cpus=num_cpus,
        concurrency=concurrency
    )

    # final_ds.write_parquet(str(production_path))
