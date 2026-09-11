import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

http = requests.Session()

retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429,500,502,503,504],
    allowed_methods=["HEAD","GET","POST","OPTIONS"]
)

adapter = HTTPAdapter(max_retries=retry_strategy)
http.mount("https://", adapter)
http.mount("http://", adapter)
