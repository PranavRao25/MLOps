from pyspark.sql import functions as F
from spark_config import create_spark_session
import yaml
from pathlib import Path
import time
import json
from data_clean import yellow_apply_clean, green_apply_clean
from data_join import detect_skew, sort_merge_join, broadcast_join, salted_join
from data_features import *

parent = Path(__file__).resolve().parent.parent.parent
with open(parent / "config.yaml") as f:
    configs = yaml.full_load(f)

raw_path = Path(configs["data"]["raw"])

JOIN_KEY          = configs["data"]["join_key"]
PARTITION_COL     = configs["data"]["partition_col"]
GROUP_COL         = configs["data"]["group_col"]
N_PARTITIONS      = configs['spark']['n_partitions']
SALT_BUCKETS      = configs["spark"]['salt_buckets']
SKEW_THRESHOLD    = configs['spark']['skew_threshold']

def is_skewed(df, join_key: str, threshold: float = SKEW_THRESHOLD) -> bool:
    total = df.count()
    top_count = (
        df.groupBy(join_key)
          .count()
          .agg(F.max("count").alias("max_count"))
          .collect()[0]["max_count"]
    )
    ratio = top_count / total if total > 0 else 0
    print(f"Skew check — top key ratio: {ratio:.4f} (threshold: {threshold})")
    return ratio > threshold

def is_small_table(df, max_bytes: int = 200 * 1024 * 1024) -> bool:
    """Rough size estimate via plan stats (best effort)."""
    try:
        plan = df._jdf.queryExecution().optimizedPlan()
        stats = plan.stats()
        size = stats.sizeInBytes()
        print(f"Estimated table size: {size / 1024 / 1024:.1f} MB")
        return size < max_bytes
    except Exception:
        return False

def append_spatiotemporal_keys(df: DataFrame, time_resolution: str = "hour") -> DataFrame:
    """
    Discretizes the continuous timestamp to create a rigid temporal grid.
    time_resolution accepts: 'hour', 'minute', 'second', etc.
    """
    return df.withColumn(
        "time_bucket", 
        F.date_trunc(time_resolution, F.col("pickup_datetime"))
    )

if __name__ == "__main__":
    spark = create_spark_session()
    
    time_yellow_start = time.time()
    yellow_raw_df = spark.read.option("mergeSchema", "true").parquet(str(raw_path / "yellow")).limit(500_000)
    yellow_raw_df = yellow_raw_df.repartition(8)
    yellow_cleaned_df = yellow_apply_clean(yellow_raw_df)
    time_yellow_end = time.time()
    # yellow_cleaned_df.coalesce(4).write.mode("overwrite").option("compression", "zstd").parquet(str(processed_path / "yellow")) # type: ignore

    time_green_start = time.time()
    green_raw_df = spark.read.option("mergeSchema", "true").parquet(str(raw_path / "green")).limit(500_000)
    green_raw_df = green_raw_df.repartition(8)
    green_cleaned_df = green_apply_clean(green_raw_df)
    time_green_end = time.time()
    # green_cleaned_df.coalesce(4).write.mode("overwrite").option("compression", "zstd").parquet(str(processed_path / "green")) # type: ignore
    
    dic = {
        "framework": "spark",
        "clean": {
            "yellow": float(time_yellow_end - time_yellow_start),
            "green": float(time_green_end - time_green_start)
        }
    }

    time_yellow_start = time.time()
    time_green_start = time.time()
    print("\n[1/6] Ingesting tables...")

    yellow = yellow_cleaned_df
    green = green_cleaned_df

    # yellow = spark.read.option("mergeSchema", "false").parquet(str(yellow_path)).limit(500_000)
    # green = spark.read.option("mergeSchema", "false").parquet(str(green_path)).limit(500_000)

    print(f"  yellow : {yellow.count():,} rows")
    print(f"  green    : {green.count():,} rows")

    print(f"\n[2/6] Checking for key skew on '{JOIN_KEY}'...")
    detect_skew(yellow, JOIN_KEY, top_n=5)

    # print("\n[3/5] Joining tables...")
    # y_alias = yellow.alias("yellow")
    # g_alias = green.alias("green")

    # if is_small_table(green):
    #     print("  Strategy: BROADCAST JOIN (green is small)")
    #     joined = broadcast_join(y_alias, g_alias, JOIN_KEY, join_type="left")
    # elif is_skewed(yellow, JOIN_KEY):
    #     print(f"  Strategy: SALTED JOIN ({SALT_BUCKETS} buckets)")
    #     joined = salted_join(
    #         y_alias, g_alias,
    #         join_key=JOIN_KEY,
    #         salt_buckets=SALT_BUCKETS,
    #         join_type="inner",
    #         n_partitions=N_PARTITIONS,
    #     )
    # else:
    #     print(f"  Strategy: SORT-MERGE JOIN ({N_PARTITIONS} partitions)")
    #     joined = sort_merge_join(
    #         y_alias, g_alias,
    #         join_key=JOIN_KEY,
    #         join_type="inner",
    #         n_partitions=N_PARTITIONS,
    #     )

    # joined.cache()
    # joined_count = joined.count()          # materialise the cache
    # print(f"  Joined rows : {joined_count:,}")

    print("\n[3/6] Discretizing Spatio-Temporal Grid & Row Features...")
    
    yellow_grid = append_spatiotemporal_keys(yellow, time_resolution="hour")
    green_grid = append_spatiotemporal_keys(green, time_resolution="hour")

    # Calculate row-level features BEFORE aggregation
    yellow_enriched = compute_row_features(yellow_grid)
    green_enriched = compute_row_features(green_grid)

    print("\n[4/6] Aggregating Hourly Zone Statistics...")
    
    # Squash the N x M explosion into 1 row per zone/hour
    yellow_agg = aggregate_zone_stats(yellow_enriched, prefix="y")
    green_agg = aggregate_zone_stats(green_enriched, prefix="g")

    print("\n[5/6] Executing 1-to-1 Composite Join...")
    
    # Perform a clean 1-to-1 join. 
    # 'outer' is used to retain zones that only had one type of taxi during that hour.
    joined = yellow_agg.join(
        green_agg, 
        on=["PULocationID", "time_bucket"], 
        how="outer" 
    )
    
    joined.cache()
    print(f"  Joined aggregated rows: {joined.count():,}")

    print(f"\n[6/6] Writing final aggregated dataset to disk...")
    
    # Calculate a revenue tier based on the aggregated average fares
    joined = joined.withColumn(
        "revenue_tier",
        F.when(F.coalesce(F.col("y_avg_fare"), F.col("g_avg_fare")) >= 50, "High")
         .when(F.coalesce(F.col("y_avg_fare"), F.col("g_avg_fare")) >= 20, "Medium")
         .otherwise("Low")
    )

    # (
    #     joined
    #     .repartition(8, PARTITION_COL)
    #     .write
    #     .partitionBy(PARTITION_COL)
    #     .mode("overwrite")
    #     .option("compression", "zstd")  # <-- Force ZStandard to bypass the Snappy/Java 21 JNI bug
    #     .parquet(str(production_path / "aggregated_features"))
    # )

    joined.unpersist()
    # enriched_yellow.unpersist()
    # enriched_green.unpersist()

    time_yellow_end = time.time()
    time_green_end = time.time()

    dic["join"] = {
        "yellow": float(time_yellow_end - time_yellow_start),
        "green": float(time_green_end - time_green_start)
    }

    with open(parent / "spark_metrics.json", "w") as f:
        json.dump(dic, f)

    print("\n Pipeline complete.")
    spark.stop()
