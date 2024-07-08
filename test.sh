echo "Running API test for transactions by category"
curl "http://localhost:8000/transactions/category/UNVALIDATED" -H "X-API-Key: 1234"
echo "Running API test for transactions by category by date for June"
curl "http://localhost:8000/categories/summary/start_date=2024-06-01&end_date=2024-06-30" -H "X-API-Key: 1234"
echo "Running API test for transactions per category daily for June"
curl "http://localhost:8000/counterparts/category_daily/UNVALIDATED/start_date=2024-06-01&end_date=2024-06-30" -H "X-API-Key: 1234"
echo "Unique counterpart names per category for June"
curl "http://localhost:8000/categories/summary?start_date=2023-01-01&end_date=2023-12-31" -H "X-API-Key: 1234"