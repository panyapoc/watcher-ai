import boto3
import os

TABLENAME = os.environ['NOTICERESULT_TABLE_NAME']

#init client
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(TABLENAME)

import json
def handler(event, context):
    # Log the event argument for debugging and for use in local development.
    print(json.dumps(event))
    response = table.scan()
    data = response['Items']

    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])



    # return http 200 json body with CORS header
    return {
        'statusCode': 200,
        'body': json.dumps(data),
        'headers': {
            'Access-Control-Allow-Origin': '*',
        }
    }
