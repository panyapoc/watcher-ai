import json
import boto3
import os

sns = boto3.client('sns')

# enviroment varible 
SNS_ARN = os.environ['NOTICEREADY_TOPIC_ARN']

def handler(event, context):
    # Log the event argument for debugging and for use in local development.
    # print(json.dumps(event))

    # http post body
    body = ''

    try:
        body = json.loads(event['body'])
    except:
        pass


    print("@@@@@@push to SNS@@@@@@")
    print(body['Message'])
    sns.publish(
        TopicArn=SNS_ARN,
        Message=body['Message']
    )

    return {
        'statusCode': 200,
        'body': json.dumps("recieved")
    }