# from airflow.utils.email import send_email
# from airflow.decorators import task
# from airflow.exceptions import AirflowFailException
# import requests
# from bs4 import BeautifulSoup



# @task(pool="scraper_pool", on_failure_callback=alert_broken_link)
# def scrape_target_url(url: str):
#     try:
#         response = requests.get(url, timeout=10)

#         if response.status_code == 404:
#             print(f"404 Not Found for {url}")
            

#             return None
        
#         response.raise_for_status()
    

#     soup = BeautifulSoup(response.text, "html.parser")
#     images = [img.get("src") for img in soup.find_all("img") if img.get("src")]

#     return {
#         "url": url,
#         "images": images
#     }
