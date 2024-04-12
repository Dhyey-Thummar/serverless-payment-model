from dataclasses import dataclass, field
from uuid import uuid4
import boto3
import json

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
    table.put_item(
        Item={
            'id': 'user1',
            'balance': 100
        }
    )
    table.put_item(
        Item={
            'id': 'user2',
            'balance': 200
        }
    )
    table.put_item(
        Item={
            'id': 'user3',
            'balance': 300
        }
    )
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

def transfer(event, context):
    print("Transferring money")
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('users')
    body = json.loads(event['body'])
    sender = body['sender']
    receiver = body['receiver']

    response = table.get_item( Key={'id': sender})
    if 'Item' not in response:
        return {
            'statusCode': 400,
            'body': 'Sender not found'
        }
    sender_balance = response['Item']['balance']
    response = table.get_item( Key={'id': receiver})
    if 'Item' not in response:
        return {
            'statusCode': 400,
            'body': 'Receiver not found'
        }
    receiver_balance = response['Item']['balance']

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
    
    sender_balance -= amount
    receiver_balance += amount

    table.update_item( Key={'id': sender}, UpdateExpression='SET balance = :val1', ExpressionAttributeValues={':val1': sender_balance})
    table.update_item( Key={'id': receiver}, UpdateExpression='SET balance = :val1', ExpressionAttributeValues={':val1': receiver_balance})
    
    message = 'Transfered ' + str(amount) + ' from ' + sender + ' to ' + receiver + '. New balance of ' + sender + ' is ' + str(sender_balance) + ' and of ' + receiver + ' is ' + str(receiver_balance)
    return {
        'statusCode': 200,
        'body': message
    }