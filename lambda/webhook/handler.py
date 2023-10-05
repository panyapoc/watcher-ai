import json
import boto3
import os

sns = boto3.client('sns')

# enviroment varible 
SNS_ARN = os.environ['NOTICEREADY_TOPIC_ARN']

def handler(event, context):
    # Log the event argument for debugging and for use in local development.
    print(json.dumps(event))

    # http post body
    body = event['body']
    
    json_body = json.loads(body)
    message = json_body['Message']


    print("@@@@@@push to SNS@@@@@@")
    print(message)
    # print(body['Message'])
    sns.publish(
        TopicArn=SNS_ARN,
        Message=message
    )

    return {
        'statusCode': 200,
        'body': json.dumps("recieved")
    }