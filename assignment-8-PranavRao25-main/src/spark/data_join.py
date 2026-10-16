from pyspark.sql import functions as F
from pyspark.sql import DataFrame, SparkSession

def sort_merge_join(
    left: DataFrame,
    right: DataFrame,
    join_key: str,
    join_type: str = "inner",
    n_partitions = 16):
    
    left_p = left.repartition(n_partitions, join_key)
    right_p = right.repartition(n_partitions, join_key)
    return left_p.join(right_p, on=join_key, how=join_type)

def salted_join(
    left: DataFrame,
    right: DataFrame,
    join_key,
    salt_buckets = 8,
    join_type = "inner",
    n_partitions = 16):

    left_salted = left.withColumn(
        "_salt", (F.rand() * salt_buckets).cast("int")
    ).withColumn(
        "_salted_key", F.concat_ws("_", F.col(join_key).cast("string"), F.col("_salt"))
    )
    
    right_exploded = right.withColumn(
        "_salt_array", F.array([F.lit(i) for i in range(salt_buckets)])
    ).withColumn(
        "_salt", F.explode("_salt_array")
    ).withColumn(
        "_salted_key", F.concat_ws("_", F.col(join_key).cast("string"), F.col("_salt"))
    )
    
    joined = (
        left_salted.repartition(n_partitions, "_salted_key")
        .join(
            right_exploded.repartition(n_partitions, "_salted_key"),
            on="_salted_key",
            how=join_type
        )
        .drop("_salt", '_salted_key')
        .drop(right_exploded[join_key])
    )

    cleaned_join = (
        joined.drop("_salt", "_salt_array", "_salted_key")
        .drop(right_exploded[join_key]) 
    )

    return joined

def broadcast_join(
    large: DataFrame,
    small: DataFrame,
    join_key,
    join_type = "inner"):
    
    return large.join(F.broadcast(small), on=join_key, how=join_type)

def write_bucketed_table(
    df: DataFrame,
    path,
    bucket_col,
    spark: SparkSession,
    n_buckets = 16,
    table_name = "bucketed_table"
    ):

    df.write.format("parquet").bucketBy(n_buckets, bucket_col).sortBy(bucket_col)\
        .mode("overwrite").saveAsTable(table_name)

def bucketed_join(
    spark,
    left_table,
    right_table,
    join_key,
    join_type = "inner"
    ):

    left = spark.table(left_table)
    right = spark.table(right_table)

    spark.conf.set("spark.sql.adaptive.enabled", "false")
    result = left.join(right, on=join_key, how=join_type)
    spark.conf.set("spark.sql.adaptive.enabled", "true")

    return result

def detect_skew(df: DataFrame, join_key: str, top_n: int = 10):
    """
    Triggers a partial action to calculate the frequency of join keys,
    helping identify unbalanced partitions prior to a sort-merge join.
    """
    skew_df = (
        df.groupBy(join_key)
        .count()
        .orderBy(F.desc("count"))
        .limit(top_n)
    )
    skew_df.show()
    return skew_df
