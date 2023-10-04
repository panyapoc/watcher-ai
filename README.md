# WatcherAI


| Description| Code | 
| ————— | ————— |
| Create a virtual environment called venv | `virtualenv venv` | 
| Activate the virtual environment | `. venv/bin/activate` |
| See installed | Sbi`pip freeze` |
| Create a requirements file | `pip freeze > requirements.txt` |
| Deactivate the virtual environement | `deactivate` |
| Remove the virtual environment | `rm -r venv` |
| To load pip file | `pip install -r requirements.txt ` |



TEST ASYNC INVOKE
```
aws lambda invoke \
  --function-name watcher-ai-newNoticeFunction-QTpYWCRyvfnE  \
      --invocation-type Event \
          --cli-binary-format raw-in-base64-out \
              --payload '{"Records":[{"EventSource":"aws:sns","EventVersion":"1.0","EventSubscriptionArn":"arn:aws:sns:us-east-1::ExampleTopic","Sns":{"Type":"Notification","MessageId":"95df01b4-ee98-5cb9-9903-4c221d41eb5e","TopicArn":"arn:aws:sns:us-east-1:123456789012:ExampleTopic","Subject":"example subject","Message":"example message","Timestamp":"1970-01-01T00:00:00.000Z","SignatureVersion":"1","Signature":"EXAMPLE","SigningCertUrl":"EXAMPLE","UnsubscribeUrl":"EXAMPLE","MessageAttributes":{"Test":{"Type":"String","Value":"TestString"},"TestBinary":{"Type":"Binary","Value":"TestBinary"}}}}]}' response.json --region us-west-2
  
```