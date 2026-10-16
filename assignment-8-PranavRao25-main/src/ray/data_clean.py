# import ray
# import typing
# from ray import dashboard
# import yaml
# import pandas as pd
# import logging
# from pathlib import Path

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# parent = Path(__file__).resolve().parent.parent
# with open(parent / "config.yaml") as f:
#     configs = yaml.full_load(f)

# parent_path = parent / configs["data"]["raw"]
# processed_path = parent / configs["data"]["processed"]
# features = configs["data"]["labels"]

# system_configs = configs["ray"]["system"]
# BATCH_SIZE = system_configs["batch_size"]
# num_cpus = system_configs["num_cpus"]
# concurrency = system_configs["concurrency"]

# class DataCleaner:
#     # TODO: CHECK FOR CLEANING TASKS
#     def __init__(self) -> None:
#         pass

#     def __call__(self, batch: pd.DataFrame) -> pd.DataFrame:
#         # clean the data domain specific way
#         return batch

# def filter_null(batch: pd.DataFrame):
#     return batch.dropna(subset=features).drop_duplicates(subset=features).dropna()

# def remove_duplicates(batch: pd.DataFrame):
#     return batch.drop_duplicates()

# def format_timestamps(batch: pd.DataFrame):
#     for col in ["tpep_pickup_datetime", "tpep_dropoff_datetime"]:
#         if col in batch:
#             batch[col] = pd.to_datetime(batch[col], errors="coerce")
#     return batch

# def process(path):
#     logger.info(f"Processing {path}")

#     ds = ray.data.read_parquet(path)
#     ds = (
#         ds
#         .map_batches(filter_null, batch_format="pandas") # type: ignore
#         .map_batches(remove_duplicates, batch_format="pandas") # type: ignore
#         .map_batches(format_timestamps, batch_format="pandas") # type: ignore
#         .map_batches(DataCleaner, batch_format="pandas") # type: ignore
#     )
#     return ds

# @ray.remote
# def spread(path):
#     try:
#         ds = process(path)
#         out = str(Path(processed_path) / Path(path).stem)
#         ds.write_parquet(out)
#         return f"OK: {path}"
#     except Exception as e:
#         return f"Failed {path} - {e}"

# def process_data(ds):
#     ds = (
#         ds
#         .map_batches(filter_null, batch_format="pandas", num_cpus=num_cpus, concurrency=concurrency) # type: ignore
#         .map_batches(remove_duplicates, batch_format="pandas", num_cpus=num_cpus, concurrency=concurrency) # type: ignore
#         .map_batches(format_timestamps, batch_format="pandas", num_cpus=num_cpus, concurrency=concurrency) # type: ignore
#         .map_batches(DataCleaner, batch_format="pandas", num_cpus=num_cpus, concurrency=concurrency) # type: ignore
#     )
#     return ds

# if __name__ == "__main__":
#     dashboard_system = configs["ray"]["dashboard"]
#     master_system = configs["ray"]["master"]
#     master_ip, master_port = master_system["ip"], master_system["port"]

#     # ray start --head --port=<master_port> --dashboard-host=<dashboard_ip>
#     # ray start --adress="<master_ip>:<master_port>"

#     # USE NFS FOR SHARED DATA

#     ray.init(address=f"ray://{master_ip}:10001")

#     ds = ray.data.read_parquet(str(parent_path))
#     ds = process_data(ds)
#     ds.write_parquet(str(processed_path))

#     # parquet_files = [str(p) for p in parent_path.iterdir() if p.is_file() and p.suffix == ".parquet"]
    
#     # futures = [spread.remote(p) for p in parquet_files]

#     # results = ray.get(futures)
#     # for r in results:
#     #     logger.info(r)

import ray
import yaml
import pandas as pd
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

parent = Path(__file__).resolve().parent.parent.parent
with open(parent / "config.yaml") as f:
    configs = yaml.full_load(f)

processed_path = parent / configs["data"]["processed"]
features = configs["data"]["labels"]

system_configs = configs["ray"]["system"]
BATCH_SIZE = system_configs["batch_size"]
num_cpus = system_configs["num_cpus"]
concurrency = system_configs["concurrency"]

class UnifiedDataCleaner:
    def __init__(self, features: list) -> None:
        self.features = features

    def __call__(self, batch: pd.DataFrame) -> pd.DataFrame:
        if "tpep_pickup_datetime" in batch.columns:
            batch.rename(columns={
                "tpep_pickup_datetime": "pickup_datetime",
                "tpep_dropoff_datetime": "dropoff_datetime"
            }, inplace=True)
        elif "lpep_pickup_datetime" in batch.columns:
            batch.rename(columns={
                "lpep_pickup_datetime": "pickup_datetime",
                "lpep_dropoff_datetime": "dropoff_datetime"
            }, inplace=True)

        batch["pickup_datetime"] = pd.to_datetime(batch["pickup_datetime"], errors="coerce")
        batch["dropoff_datetime"] = pd.to_datetime(batch["dropoff_datetime"], errors="coerce")
        batch.dropna(subset=["pickup_datetime", "dropoff_datetime"], inplace=True)

        batch["pickup_hour"] = batch["pickup_datetime"].dt.floor("h")

        valid_features = [f for f in self.features if f in batch.columns]
        if valid_features:
            batch.dropna(subset=valid_features, inplace=True)
            batch.drop_duplicates(subset=valid_features, inplace=True)
        
        if "trip_distance" in batch.columns:
            batch = batch[batch["trip_distance"] > 0]

        return batch

def process_data(ds: ray.data.Dataset) -> ray.data.Dataset:
    ds = ds.map_batches(
        UnifiedDataCleaner(features=features), # type: ignore
        batch_size=BATCH_SIZE,
        batch_format="pandas",
        num_cpus=num_cpus,
        concurrency=concurrency
    )
    return ds
