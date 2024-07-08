#preload the transactions

# CSV file name
csv_file="txns.csv"

# Function to send curl request
send_curl_request() {
    local counterpartName="$1"
    local transactionTimeUtc="$2"
    local amount="$3"
    local transactionType="$4"
    local transactionId="$5"
#Categorisation is an external process that we have to handle after the data is in place and the logic has to be listed
    curl -X POST "http://localhost:80/transaction/UNVALIDATED" \
         -H "Content-Type: application/json" \
         -H "X-API-Key: 1234" \
         -d "{
             \"transactionId\": \"$transactionId\",
             \"amount\": $amount,
             \"counterpartName\": \"$counterpartName\",
             \"transactionTimeUtc\": \"$transactionTimeUtc\",
             \"transactionType\": \"$transactionType\"
         }"
    echo "" # Add a newline for readability
}

# Skip the header line
tail -n +2 "$csv_file" | while IFS=',' read -r transactionId amount counterpartName transactionTimeUtc transactionType
do
	echo "load the .csv"
    # Remove any surrounding quotes from fields
    transactionId=$(echo "$transactionId" | tr -d '"')
    amount=$(echo "$amount" | tr -d '"')
    counterpartName=$(echo "$counterpartName" | tr -d '"')
    transactionTimeUtc=$(echo "$transactionTimeUtc" | tr -d '"')
    transactionType=$(echo "$transactionType" | tr -d '"')

    # Send curl request for each row
    send_curl_request "$transactionId" "$amount" "$counterpartName" "$transactionTimeUtc" "$transactionType"
done