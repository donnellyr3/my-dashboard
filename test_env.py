import os
from dotenv import load_dotenv

load_dotenv()

EBAY_ACCESS_TOKEN = os.getenv("EBAY_ACCESS_TOKEN")
EBAY_REFRESH_TOKEN = os.getenv("EBAY_REFRESH_TOKEN")

print("Access Token:", EBAY_ACCESS_TOKEN[:40], "...")
print("Refresh Token:", EBAY_REFRESH_TOKEN[:40], "...")

