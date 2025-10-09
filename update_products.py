import requests
import schedule
import time

# Your Render API URL
API_URL = "https://my-dashboard-tqtg.onrender.com/api/products"

# Example product updates
products_to_update = [
    {"name": "Test Product", "price": 12.99},  # New price
    {"name": "Another Product", "price": 18.50}  # New price
]

def update_products():
    for product in products_to_update:
        # Add or update product
        response = requests.post(API_URL, json=product)
        if response.status_code == 201:
            print(f"Added/Updated product: {product['name']}")
        else:
            print(f"Failed to update {product['name']}: {response.text}")

# Schedule updates every 10 minutes
schedule.every(10).minutes.do(update_products)

print("Auto-update script running...")
update_products()  # Run immediately on start

# Keep script running
while True:
    schedule.run_pending()
    time.sleep(1)

