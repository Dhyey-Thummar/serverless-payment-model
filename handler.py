from dataclasses import dataclass, field
from uuid import uuid4
import boto3
import json
import time

MAX_RETRIES = 3
RETRY_DELAY = 0.5  # Delay in seconds between retries

def initTable(event, context):
    print("Creating table")
    
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.create_table(
        TableName='users',
        KeySchema=[
            {
                'AttributeName': 'id',
                'KeyType': 'HASH'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'id',
                'AttributeType': 'S'
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )
    table.meta.client.get_waiter('table_exists').wait(TableName='users')
    print("Table created")

    # Add some data
    table = dynamodb.Table('users')

    no_of_users = 10
    for i in range(no_of_users):
        user = {
            'id': str(user + str(i)),
            'balance': 1000
        }
        table.put_item(Item=user)

    return {
        'statusCode': 200,
        'body': 'Table created'
    }

def getBalance(event, context):
    print("Getting balance")
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('users')

    query_params = event['queryStringParameters']
    user_id = str(query_params['id'])
    response = table.get_item(
        Key={
            'id': user_id
        }
    )
    item = response['Item']
    balance = item['balance']
    return {
        'statusCode': 200,
        'body': 'user ' + user_id + ' has balance ' + str(balance)
    }

def perform_transaction(sender, receiver, amount, sender_balance, receiver_balance):
    client = boto3.client('dynamodb')
    
    for _ in range(MAX_RETRIES):
        try:
            response = client.transact_write_items(
                TransactItems=[
                    {
                        'Update': {
                            'TableName': 'users',
                            'Key': {
                                'id': {'S': sender}
                            },
                            'UpdateExpression': 'SET balance = :val1',
                            'ExpressionAttributeValues': {
                                ':val1': {'N': str(sender_balance)}
                            }
                        }
                    },
                    {
                        'Update': {
                            'TableName': 'users',
                            'Key': {
                                'id': {'S': receiver}
                            },
                            'UpdateExpression': 'SET balance = :val1',
                            'ExpressionAttributeValues': {
                                ':val1': {'N': str(receiver_balance)}
                            }
                        }
                    }
                ]
            )
            return True, response
        
        except client.exceptions.ProvisionedThroughputExceededException:
            # If ProvisionedThroughputExceededException is raised, retry after delay
            time.sleep(RETRY_DELAY)
            continue
        
        except Exception as e:
            # For other exceptions, return False and the exception message
            return False, str(e)
    
    # If all retries fail
    return False, "Failed to perform transaction after retries"

def transfer(event, context):
    print("Transferring money")
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('users')
    body = json.loads(event['body'])
    sender = body['sender']
    receiver = body['receiver']

    # Get sender's balance
    try:
        response = table.get_item(Key={'id': sender})
        if 'Item' not in response:
            return {
                'statusCode': 400,
                'body': 'Sender not found'
            }
        sender_balance = response['Item']['balance']
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f"Failed to get sender's balance: {str(e)}"
        }

    # Get receiver's balance
    try:
        response = table.get_item(Key={'id': receiver})
        if 'Item' not in response:
            return {
                'statusCode': 400,
                'body': 'Receiver not found'
            }
        receiver_balance = response['Item']['balance']
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f"Failed to get receiver's balance: {str(e)}"
        }

    amount = int(body['amount'])
    if amount <= 0:
        return {
            'statusCode': 400,
            'body': 'Amount should be greater than 0'
        }
    
    if sender_balance < amount:
        return {
            'statusCode': 400,
            'body': 'Insufficient balance'
        }
    
    # Update balances
    sender_balance -= amount
    receiver_balance += amount

    # Perform transaction
    success, response = perform_transaction(sender, receiver, amount, sender_balance, receiver_balance)
    
    if success:
        message = f"Transferred {amount} from {sender} to {receiver}. New balance of {sender} is {sender_balance} and of {receiver} is {receiver_balance}"
        return {
            'statusCode': 200,
            'body': message
        }
    else:
        return {
            'statusCode': 500,
            'body': f"Transaction failed: {response}"
        }