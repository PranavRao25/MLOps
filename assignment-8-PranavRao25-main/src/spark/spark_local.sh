#!/usr/bin/env bash

# submit.sh
# ---------
# Local spark-submit wrapper for the Taxi Data Pipeline.

set -euo pipefail

if [ -z "$1" ]; then
  echo "Error: No PySpark script provided."
  echo "Usage: ./spark_local.sh <script_name.py>"
  exit 1
fi

MASTER="local[*]"      
DRIVER_MEMORY="8g"
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET_SCRIPT=$1
MAIN_SCRIPT="${APP_DIR}/${TARGET_SCRIPT}"
# MAIN_SCRIPT="${APP_DIR}/join_main.py"
PY_FILES="${APP_DIR}/spark_config.py,${APP_DIR}/data_join.py,${APP_DIR}/data_features.py,${APP_DIR}/data_clean.py"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Submitting Local Pipeline: ${TARGET_SCRIPT}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

CORES=$(nproc)

spark-submit \
  --master "${MASTER}" \
  --driver-memory "${DRIVER_MEMORY}" \
  \
  --conf spark.sql.shuffle.partitions=$((CORES * 2)) \
  --conf spark.default.parallelism=$((CORES * 2)) \
  --conf spark.memory.offHeap.enabled=true \
  --conf spark.memory.offHeap.size=2g \
  --conf spark.sql.adaptive.enabled=true \
  \
  --py-files "${PY_FILES}" \
  "${MAIN_SCRIPT}"

# echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
# echo "  Submitting Local Taxi Pipeline"
# echo "  Master          : ${MASTER}"
# echo "  Driver Memory   : ${DRIVER_MEMORY}"
# echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# spark-submit \
#   --master "${MASTER}" \
#   --driver-memory "${DRIVER_MEMORY}" \
#   \
#   --conf spark.sql.shuffle.partitions=$((CORES * 2)) \
#   --conf spark.default.parallelism=$((CORES * 2)) \
#   --conf spark.memory.offHeap.enabled=true \
#   --conf spark.memory.offHeap.size=2g \
#   --conf spark.sql.adaptive.enabled=true \
#   --conf spark.serializer=org.apache.spark.serializer.KryoSerializer \
#   \
#   --py-files "${PY_FILES}" \
#   "${MAIN_SCRIPT}"
