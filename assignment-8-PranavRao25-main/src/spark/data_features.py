# from pyspark.sql import DataFrame
# from pyspark.sql.window import Window
# from pyspark.sql import functions as F

# def enrich_taxi_data(df: DataFrame, alias: str, group_col: str, prefix_type: str = "") -> DataFrame:
#     """
#     Computes row-level features and Window-based aggregates natively via Catalyst.
#     """

#     w_group = Window.partitionBy(F.col(group_col))
    
#     return df.withColumn(
#         "duration_sec",
#         F.col(f"{alias}.dropoff_datetime").cast("long") - F.col(f"{alias}.pickup_datetime").cast("long")
#     ).withColumn(
#         "avg_speed_per_hr",
#         F.when(F.col("duration_sec") > 0, (F.col(f"{alias}.trip_distance") * 3600) / F.col("duration_sec")).otherwise(0.0)
#     ).withColumn(
#         "revenue_tier",
#         F.when(F.col(f"{alias}.total_amount") >= 50, "High")
#          .when(F.col(f"{alias}.total_amount") >= 20, "Medium")
#          .otherwise("Low")
#     ).withColumn(
#         "zone_avg_amount", 
#         F.mean(f"{alias}.total_amount").over(w_group)
#     ).withColumn(
#         "zone_total_passengers", 
#         F.sum(f"{alias}.passenger_count").over(w_group)
#     )

# def yellow_map_features(df: DataFrame) -> DataFrame:
#     """
#     Computes derived features using native Catalyst expressions.
#     """
#     return df.withColumn(
#         "duration",
#         F.col("tpep_dropoff_datetime").cast("long") - F.col("tpep_pickup_datetime").cast("long")
#     ).withColumn(
#         "avg_speed_per_hr",
#         F.when(
#             F.col("duration") > 0, 
#             (F.col("trip_distance") * 3600) / F.col("duration")
#         ).otherwise(0.0)
#     )

# def yellow_reduce_features(df: DataFrame) -> DataFrame:
#     """
#     Performs a global aggregation across all partitions, returning a single DataFrame.
#     """
#     return df.groupBy("VendorID").agg(
#         F.mean("total_amount").alias("avg_total_amount"),
#         F.sum("passenger_count").alias("total_passenger_count")
#     )

# def green_map_features(df: DataFrame) -> DataFrame:
#     """
#     Computes derived features for the green taxi dataset using its specific timestamp prefixes.
#     """
#     return df.withColumn(
#         "duration",
#         F.col("lpep_dropoff_datetime").cast("long") - F.col("lpep_pickup_datetime").cast("long")
#     ).withColumn(
#         "avg_speed_per_hr",
#         F.when(
#             F.col("duration") > 0, 
#             (F.col("trip_distance") * 3600) / F.col("duration")
#         ).otherwise(0.0)
#     )

# def green_reduce_features(df: DataFrame) -> DataFrame:
#     """
#     Performs a global aggregation across all partitions, returning a single DataFrame.
#     """
#     return df.groupBy("VendorID").agg(
#         F.mean("total_amount").alias("avg_total_amount"),
#         F.sum("passenger_count").alias("total_passenger_count")
#     )

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

def compute_row_features(df: DataFrame) -> DataFrame:
    """
    Computes trip-level features natively via Catalyst before aggregation.
    """
    return df.withColumn(
        "duration_sec",
        F.col("dropoff_datetime").cast("long") - F.col("pickup_datetime").cast("long")
    ).withColumn(
        "avg_speed_per_hr",
        F.when(
            F.col("duration_sec") > 0, 
            (F.col("trip_distance") * 3600) / F.col("duration_sec")
        ).otherwise(0.0)
    )

def aggregate_zone_stats(df: DataFrame, prefix: str) -> DataFrame:
    """
    Reduces the DataFrame to 1 row per Location-Hour grid via HashAggregate.
    """
    return df.groupBy("PULocationID", "time_bucket").agg(
        F.sum("passenger_count").alias(f"{prefix}_total_passengers"),
        F.mean("total_amount").alias(f"{prefix}_avg_fare"),
        F.mean("avg_speed_per_hr").alias(f"{prefix}_avg_speed"),
        F.count("*").alias(f"{prefix}_trip_count")
    )
