import requests

# API base URL
base_url = "http://localhost:80"

# API key
api_key = "1234"

# Headers
headers = {
    "X-API-Key": api_key
}

# Test for month of July
print("Running API test for transactions by category by date for June")
response = requests.get(
    f"{base_url}/categories/summary/date_range",
    params={
        "start_date": "2000-01-01",
        "end_date": "2024-12-31"
    },
    headers=headers
)
print(response.text)

print("Running API test for transactions per category daily for June")
response = requests.get(
    f"{base_url}/counterparts/category_daily/Retail/date_range",
    params={
        "start_date": "2000-01-01",
        "end_date": "2024-12-31"
    },
    headers=headers
)
print(response.text)

print("Unique counterpart names per category for June")
response = requests.get(
    f"{base_url}/counterparts/Retail",
    params={
        "start_date": "2023-06-01",
        "end_date": "2023-06-30"
    },
    headers=headers
)
print(response.text)