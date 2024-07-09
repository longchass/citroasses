import csv
import requests

# CSV file name
csv_file = "txns.csv"

# Function to send POST request
def send_post_request(counterpart_name, transaction_time_utc, amount, transaction_type, transaction_id):
    url = "http://localhost:80/transaction/"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": "1234"
    }
    payload = {
        "transactionId": transaction_id,
        "amount": amount,
        "counterpartName": counterpart_name,
        "transactionTimeUtc": transaction_time_utc,
        "transactionType": transaction_type
    }
    
    response = requests.post(url, json=payload, headers=headers)
    print(response.text)
    print()  # Add a newline for readability

# Read and process the CSV file
with open(csv_file, 'r') as file:
    csv_reader = csv.reader(file)
    next(csv_reader)  # Skip the header line
    
    print("Loading the .csv")
    for row_number, row in enumerate(csv_reader, start=2):  # Start counting from 2 to account for header
        try:
            # Only take the first 5 columns
            counterpart_name, transaction_time_utc, amount, transaction_type, transaction_id = row[:5]
            
            # Remove any surrounding quotes from fields
            transaction_id = transaction_id.strip('"')
            amount = amount.strip('"')
            counterpart_name = counterpart_name.strip('"')
            transaction_time_utc = transaction_time_utc.strip('"')
            transaction_type = transaction_type.strip('"')
            print(f"Row {row_number}: {transaction_id}, {amount}, {counterpart_name}, {transaction_time_utc}, {transaction_type}")
            # Send POST request for each row
            send_post_request(counterpart_name, transaction_time_utc, amount, transaction_type, transaction_id)
        except ValueError as e:
            print(f"Error processing row {row_number}: {e}")
            print(f"Row content: {row}")
            continue  # Skip this row and continue with the next
