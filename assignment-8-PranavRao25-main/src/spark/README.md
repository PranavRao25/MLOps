# Heavy Join + Feature Engineering Pipeline

## File Structure

```
spark_join_pipeline/
├── spark_config.py        # SparkSession factory (join + AQE tuning)
├── join_strategies.py     # Sort-merge, broadcast, salted, bucketed joins
├── feature_engineering.py # Ratio, window, categorical, group features
├── main.py                # Orchestrator — ingests, joins, engineers, writes
└── submit.sh              # spark-submit wrapper
```

---

## Quick Start

```bash
# 1. Make the submit script executable
chmod +x submit.sh

# 2. Run with default paths (edit paths inside submit.sh first)
bash submit.sh

# 3. Or override paths at runtime
TRANSACTIONS_PATH=hdfs:///data/transactions.parquet \
CUSTOMERS_PATH=hdfs:///data/customers.parquet \
OUTPUT_PATH=hdfs:///data/enriched/ \
bash submit.sh
```

For local testing (no cluster):
```bash
# Edit spark_config.py → .master("local[4]")
python main.py \
  --transactions-path ./sample/transactions.parquet \
  --customers-path    ./sample/customers.parquet \
  --output-path       ./output/enriched
```

---

## Join Strategy Decision Tree

```
Is the right table < 200 MB?
├── YES → Broadcast Join        (zero shuffle, fastest)
└── NO  → Is the join key skewed?
          ├── YES → Salted Join  (splits hot keys into N buckets)
          └── NO  → Sort-Merge Join (default large-table path)

Special case: repeated joins on the same key?
          └──→ Bucketed Join    (write once, never shuffle again)
```

---

## Derived Features

| Feature | Type | Description |
|---|---|---|
| `gross_margin` | Ratio | (revenue - cost) / revenue |
| `conversion_rate` | Ratio | conversions / sessions |
| `revenue_per_conversion` | Ratio | revenue / conversions |
| `cost_per_session` | Ratio | cost / sessions |
| `revenue_x_conversion` | Interaction | revenue × conversion_rate |
| `revenue_7d_avg` | Rolling | 7-row rolling mean of revenue |
| `revenue_30d_avg` | Rolling | 30-row rolling mean |
| `sessions_7d_sum` | Rolling | 7-row rolling sum of sessions |
| `revenue_7d_stddev` | Rolling | 7-row rolling std-dev (volatility) |
| `cumulative_revenue` | Cumulative | Running total per customer |
| `revenue_lag1` / `lag7` | Lag | Previous 1 / 7 period revenue |
| `revenue_wow_change` | % Change | Week-over-week revenue delta |
| `revenue_rank` | Rank | Best revenue day rank per customer |
| `revenue_tier` | Bucket | low / medium / high / enterprise |
| `is_high_value` | Flag | cumulative revenue > 50 000 |
| `engagement_score` | Composite | Weighted combination of rate, WoW, sessions |
| `region_avg_revenue` | Group agg | Mean revenue in customer's region |
| `region_total_conversions` | Group agg | Total conversions in region |

---

## Tuning Reference

### Partitions
- `spark.sql.shuffle.partitions` = 2–4 × total executor cores
- For 2 nodes × 4 cores: **16** is a solid starting point
- Increase if you see many small tasks; decrease if tasks are too large

### Memory
- `spark.memory.fraction=0.8` — gives more heap to execution/storage
- `spark.memory.storageFraction=0.3` — 30% of managed memory for caching

### Broadcast threshold
- `spark.sql.autoBroadcastJoinThreshold` — default 10 MB, raised to 20 MB here
- Raise further (e.g. 100 MB) if your dimension table fits comfortably

### AQE (Adaptive Query Execution)
- `skewJoin.skewedPartitionFactor=5` — a partition is "skewed" if 5× median size
- `skewedPartitionThresholdInBytes=256MB` — minimum size to be considered skewed

### Salted join buckets
- `SALT_BUCKETS = 8` — try powers of 2 (4, 8, 16)
- Higher values spread hot keys more but replicate the right table more

---

## Common Issues

| Symptom | Likely Cause | Fix |
|---|---|---|
| OOM on executors | Partition too large | Increase `shuffle.partitions` |
| One task 10× slower | Key skew | Switch to salted join |
| Long GC pauses | Over-caching | Call `.unpersist()` after use |
| Broadcast timeout | Table too large to collect | Lower broadcast threshold |
| Many tiny output files | Over-partitioned write | Add `.coalesce(N)` before write |
