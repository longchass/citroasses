#curl test for month of July
echo "Running API test for transactions by category by date for June"
curl "http://localhost:80/categories/summary/date_range?start_date=2024-06-01&end_date=2024-06-30" -H "X-API-Key: 1234"
echo "Running API test for transactions per category daily for June"
curl "http://localhost:80/counterparts/category_daily/UNVALIDATED/date_range?start_date=2024-06-01&end_date=2024-06-30" -H "X-API-Key: 1234"
echo "Unique counterpart names per category for June"
curl "http://localhost:80/counterparts/category/UNVALIDATED/date_range?start_date=2024-06-01&end_date=2024-06-30" -H "X-API-Key: 1234"
