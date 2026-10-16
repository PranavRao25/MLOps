# from pyspark.sql import SparkSession

# def create_spark_session(app_name: str = "HeavyJoinFeatureEngineering") -> SparkSession:
#     spark = (
#         SparkSession.builder
#         .appName(app_name)
#         .master("spark://master-node:7077")       # replace with your master URL
#         .config("spark.executor.instances", "2")   # one executor per node
#         .config("spark.executor.cores", "4")
#         .config("spark.executor.memory", "12g")
#         .config("spark.driver.memory", "4g")
#         .config("spark.driver.maxResultSize", "2g")
#         .config("spark.default.parallelism", "16")
#         .config("spark.sql.shuffle.partitions", "16")
#         .config("spark.sql.autoBroadcastJoinThreshold", str(20 * 1024 * 1024))
#         .config("spark.sql.join.preferSortMergeJoin", "true")
#         .config("spark.sql.broadcastTimeout", "600")
#         .config("spark.sql.adaptive.enabled", "true")
#         .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
#         .config("spark.sql.adaptive.skewJoin.enabled", "true")
#         .config("spark.sql.adaptive.skewJoin.skewedPartitionFactor", "5")
#         .config("spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes", str(256 * 1024 * 1024))
#         .config("spark.memory.fraction", "0.8")
#         .config("spark.memory.storageFraction", "0.3")
#         .config("spark.sql.execution.arrow.pyspark.enabled", "true")
#         .config("spark.sql.parquet.mergeSchema", "false")
#         .config("spark.sql.parquet.filterPushdown", "true")
#         .config("spark.sql.parquet.compression.codec", "snappy")
#         .getOrCreate()
#     )

#     spark.sparkContext.setLogLevel("WARN")
#     return spark

from pyspark.sql import SparkSession
import multiprocessing

def create_spark_session(is_local: bool = True) -> SparkSession:
    # builder = SparkSession.builder.appName("Ass8")
    
    # if is_local:
    #     cores = multiprocessing.cpu_count()
        
    #     builder = (
    #         builder
    #         .master(f"local[{cores}]") 
    #         .config("spark.driver.memory", "8g")
            
    #         # CRITICAL: Spark defaults to 200 shuffle partitions. On a single machine,
    #         # this causes massive task scheduling overhead and context switching. 
    #         # Drop this to match or slightly exceed your CPU core count.
    #         .config("spark.sql.shuffle.partitions", str(cores * 2))
    #         .config("spark.memory.offHeap.enabled", "true")
    #         .config("spark.memory.offHeap.size", "2g")
    #         .config("spark.sql.adaptive.enabled", "true")
    #     )
            
    # return builder.getOrCreate()
    return SparkSession.builder.appName("ass8").getOrCreate()
