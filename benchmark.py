import requests
import time
import json

# Replace with your Lambda URL
LAMBDA_URL = "https://hkuzejabuoy45qdnfu53ha5t340jhruw.lambda-url.ap-south-1.on.aws/"

headers = {
    'Content-Type': 'application/json'
}

# Define the users and amounts for benchmarking
users = ['user1', 'user2', 'user3', 'user4']
amounts = [1]

# Number of requests to make for each combination of user and amount
num_requests = 10

latencies = []
failedCount = 0
for user in users:
    for amount in amounts:
        for _ in range(num_requests):
            data = {
                'sender': user,
                'receiver': 'user5',  # Assuming user2 is always the receiver
                'amount': amount
            }
            
            start_time = time.time()
            
            response = requests.post(LAMBDA_URL, headers=headers, data=json.dumps(data))
            
            end_time = time.time()
            
            latency = end_time - start_time
            latencies.append(latency)
            
            if response.status_code == 200:
                # print(f"Transfer successful. Latency: {latency:.4f} seconds")
                continue
            else:
                # print(f"Transfer failed. Status code: {response.status_code}, Message: {response.text}")
                failedCount += 1
                print(f"Transfer failed for sender: {user}, amount: {amount}, Status code: {response.status_code}, Message: {response.text}")
# Calculate average latency
average_latency = sum(latencies) / len(latencies)
max_latency = max(latencies)
min_latency = min(latencies)
std_dev = (sum([(x - average_latency) ** 2 for x in latencies]) / len(latencies)) ** 0.5
print(f"\nAverage latency for {num_requests} requests per user with amount 10: {average_latency:.4f} seconds")
print(f"Max latency: {max_latency:.4f} seconds")
print(f"Min latency: {min_latency:.4f} seconds")
print(f"Standard deviation: {std_dev:.4f} seconds")
print(f"Failed Count: {failedCount} out of {num_requests*len(users)*len(amounts)}")