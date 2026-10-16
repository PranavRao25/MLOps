#! /bin/bash

docker compose up
docker compose run airflow-worker airflow info --remove-orphans
docker compose down --volumes --rmi all
