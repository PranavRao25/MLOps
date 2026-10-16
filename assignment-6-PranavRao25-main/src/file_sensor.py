# from datetime import datetime, timedelta
# from airflow import DAG
# from airflow.sensors.filesystem import FileSensor
# from airflow.operators.email import EmailOperator, send_email
# import pandas as pd
# import requests
# from bs4 import BeautifulSoup
# import sqlite3
# import re
# import os
# import yaml
# from pathlib import Path
# from url_extractor import *
# from alerts import *
# from persistor import *

# parent = Path(__file__).resolve().parent.parent

# with open(parent / "config.yaml", "r") as f:
#     configs = yaml.full_load(f)
# default_args = configs["default_args"]
# default_args["retry_delay"] = timedelta(configs["default_args"]["retry_delay"])

# def alert_dry_pipeline(context):
#     task_instance = context.get("task_instance")
#     execution_date = context.get("execution_date")
#     dag_id = task_instance.dag_id
#     task_id = task_instance.task_id

#     subject = f"AIRFLOW ALERT: Dry Pipeline {dag_id}"

#     html_content = """
#         <h3>Dry Pipeline Alert</h3>
#         <p>The sensor task <b>{task_id}</b> timed out waiting for a new target list.</p>
#         <ul>
#             <li><b>DAG:</b> {dag_id}</li>
#             <li><b>Execution Date:</b> {execution_date}</li>
#             <li><b>Log URL:</b> <a href="{task_instance.log_url}">View Airflow Logs</a></li>
#         </ul>
#         <p>Please verify the upstream systems responsible for delivering the CSV.</p>
#     """

#     receipent_mail = configs["mail"]["receiver_mail"]

#     try:
#         send_email(to=receipent_mail, subject=subject, html_content=html_content)
#         print("Dry pipeline mail sent")
#     except Exception as e:
#         print(f"Failed to send mail {e}")

# with DAG(
#     dag_id="web_scraper_pipeline",
#     default_args=default_args,
#     description="Automated Web-to-DB Pipeline",
#     schedule_interval=timedelta(days=1),
#     start_date=datetime(2026, 4, 2),
#     catchup=False) as dag:

#     watch_for_target_list = FileSensor(
#         task_id="watch_for_csv_file",
#         fs_conn_id="csv_folder_conn",
#         filepath="*.csv",
#         poke_interval=60,
#         timeout=12*60*60,
#         mode="reschedule",
#         on_failure_callback=alert_dry_pipeline
#     )

#     url_list = extract_urls_from_csv("")

#     scraped_data = scrape_target_urls.expand(url=url_list)

#     persist_data(scraped_data)

#     scrape_target_url()

#     # DEFINE THE DEPENDENCIES
    