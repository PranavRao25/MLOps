import ray
import pandas as pd
import yaml
import time
import json
from pathlib import Path
from data_clean import process_data

parent = Path(__file__).resolve().parent.parent.parent
with open(parent / "config.yaml") as f:
    configs = yaml.full_load(f)

# production_path = str(parent / configs["data"]["production"])
yellow_raw = str(parent / configs["data"]["raw"] / "yellow")
green_raw = str(parent / configs["data"]["raw"] / "green")

system_configs = configs["ray"]["system"]
BATCH_SIZE = system_configs["batch_size"]
num_cpus = system_configs["num_cpus"]
concurrency = system_configs["concurrency"]

def prefix_columns(batch: pd.DataFrame, prefix: str) -> pd.DataFrame:
    rename_dict = {
        col: f"{prefix}_{col}" 
        for col in batch.columns 
        if col != "composite_key"
    }
    return batch.rename(columns=rename_dict)

def create_composite_key(batch: pd.DataFrame) -> pd.DataFrame:
    if all(k in batch.columns for k in ["PULocationID", "DOLocationID", "pickup_hour"]):
        batch["composite_key"] = (
            batch["PULocationID"].astype(str) + "_" + 
            batch["DOLocationID"].astype(str) + "_" + 
            batch["pickup_hour"].astype(str)
        )
    return batch

def derive_complex_features(batch: pd.DataFrame) -> pd.DataFrame:
    if "yellow_pickup_datetime" in batch.columns and "yellow_dropoff_datetime" in batch.columns:
        batch["yellow_duration_mins"] = (
            batch["yellow_dropoff_datetime"] - batch["yellow_pickup_datetime"]
        ).dt.total_seconds() / 60.0
        
        batch = batch[(batch["yellow_duration_mins"] > 0) & (batch["yellow_duration_mins"] < 300)]
        
        if "yellow_trip_distance" in batch.columns:
            batch["yellow_avg_speed_mph"] = batch["yellow_trip_distance"] / (batch["yellow_duration_mins"] / 60.0)
            
    if "green_pickup_datetime" in batch.columns and "green_dropoff_datetime" in batch.columns:
        batch["green_duration_mins"] = (
            batch["green_dropoff_datetime"] - batch["green_pickup_datetime"]
        ).dt.total_seconds() / 60.0
        
        batch = batch[(batch["green_duration_mins"] > 0) & (batch["green_duration_mins"] < 300)]
        
        if "green_trip_distance" in batch.columns:
            batch["green_avg_speed_mph"] = batch["green_trip_distance"] / (batch["green_duration_mins"] / 60.0)
            
    return batch

if __name__ == "__main__":
    master_system = configs["ray"]["master"]
    master_ip = master_system["ip"]

    ray.init(address=f"{master_ip}:6379")  # address=f"ray://{master_ip}:4532"

    time_yellow_start = time.time()
    time_green_start = time.time()
    ds_yellow = ray.data.read_parquet(yellow_raw)
    ds_green = ray.data.read_parquet(green_raw)

    ds_yellow_clean = process_data(ds_yellow)
    ds_green_clean = process_data(ds_green)

    ds_yellow_keyed = ds_yellow_clean.map_batches(create_composite_key, batch_format="pandas") # type: ignore
    ds_green_keyed = ds_green_clean.map_batches(create_composite_key, batch_format="pandas") # type: ignore

    ds_yellow_prefixed = ds_yellow_keyed.map_batches(
        lambda batch: prefix_columns(batch, "yellow"),  # type: ignore
        batch_format="pandas"
    )
    
    ds_green_prefixed = ds_green_keyed.map_batches(
        lambda batch: prefix_columns(batch, "green"),  # type: ignore
        batch_format="pandas"
    )
    
    joined_ds = ds_yellow_prefixed.join(
        ds_green_prefixed,
        on=["composite_key"], # type: ignore
        join_type="inner",         # Replaces Pandas' `how`
        num_partitions=200         # Mandatory: dictates the number of hash buckets for the network shuffle
    )

    final_ds = joined_ds.map_batches(
        derive_complex_features, # type: ignore
        batch_size=BATCH_SIZE,
        batch_format="pandas",
        num_cpus=num_cpus,
        concurrency=concurrency
    )

    time_yellow_end = time.time()
    time_green_end = time.time()

    dic = {
        "framework": "ray",
        "yellow": float(time_yellow_end - time_yellow_start),
        "green": float(time_green_end - time_green_start)
    }
