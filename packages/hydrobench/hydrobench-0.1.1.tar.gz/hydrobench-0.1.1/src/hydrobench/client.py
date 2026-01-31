import pocketbase
import os

#POCKETBASE_URL = os.getenv("HYDROBENCH_URL", "https://db.hydrobench.org")
POCKETBASE_URL = os.getenv("HYDROBENCH_URL", "http://127.0.0.1:8099")
anonymous_client = pocketbase.Client(POCKETBASE_URL)

