#!/usr/bin/env bash
# submit.sh
# ---------
# spark-submit wrapper for the heavy join + feature engineering pipeline.
# Run: bash submit.sh

set -euo pipefail
MASTER="spark://master-node:7077"      # or yarn / local[*] for testing
EXECUTOR_INSTANCES=2
EXECUTOR_CORES=4
EXECUTOR_MEMORY="8g"
DRIVER_MEMORY="4g"
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
MAIN_SCRIPT="${APP_DIR}/main.py"
PY_FILES="${APP_DIR}/spark_config.py,${APP_DIR}/data_join.py,${APP_DIR}/data_features.py"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Submitting Heavy Join Pipeline"
echo "  Master          : ${MASTER}"
echo "  Executors       : ${EXECUTOR_INSTANCES} × ${EXECUTOR_CORES} cores / ${EXECUTOR_MEMORY}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

spark-submit \
  --master "${MASTER}" \
  --deploy-mode client \
  --num-executors "${EXECUTOR_INSTANCES}" \
  --executor-cores "${EXECUTOR_CORES}" \
  --executor-memory "${EXECUTOR_MEMORY}" \
  --driver-memory "${DRIVER_MEMORY}" \
  \
  --conf spark.sql.adaptive.enabled=true \
  --conf spark.sql.adaptive.coalescePartitions.enabled=true \
  --conf spark.sql.adaptive.skewJoin.enabled=true \
  --conf spark.sql.autoBroadcastJoinThreshold=$((20 * 1024 * 1024)) \
  --conf spark.sql.shuffle.partitions=16 \
  --conf spark.default.parallelism=16 \
  --conf spark.memory.fraction=0.8 \
  --conf spark.sql.execution.arrow.pyspark.enabled=true \
  --conf spark.sql.parquet.filterPushdown=true \
  --conf spark.serializer=org.apache.spark.serializer.KryoSerializer \
  \
  --py-files "${PY_FILES}" \
  "${MAIN_SCRIPT}" "$@"
