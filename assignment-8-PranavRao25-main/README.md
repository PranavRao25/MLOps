[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/pesOmrUm)

# Ray

To start at host: 
```
ray start --head --node-ip-address=<host_ip>:port --dashboard-host=<ip>
```

To add another node to this Ray cluster, run
```
ray start --address='<master_ip>
```
  
To terminate the Ray runtime, run
```
ray stop
```

To view the status of the cluster, use
```
ray status
```

Common Pitfalls:
1. Ensure the python environment is same between nodes (even the python version needs to match)

# Spark

To start the host:
```
~/spark/sbin/start-master.sh --host <master_ip>
```

To stop the host:
```
~/spark/sbin/stop-master.sh
```

To start the worker:
```
~/spark/sbin/start-worker.sh spark://<master_ip>:port
```

To stop the worker:
```
~/spark/sbin/stop-worker.sh
```

To run a task:
```
spark-submit --master spark://<master_ip>:port src/spark/main.py
```

Common Pitfalls:
1. Ensure JDK and spark version is the same between the nodes