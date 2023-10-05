import json

event = {
  "Records": [
      {
          "EventSource": "aws:sns",
          "EventVersion": "1.0",
          "EventSubscriptionArn": "arn:aws:sns:us-west-2:430636640134:watcher-ai-NoticeReady-0MS3urkThRsY:4a437c1f-63bc-452a-aa95-d4a3e7eee928",
          "Sns": {
              "Type": "Notification",
              "MessageId": "be73d267-adc0-5c63-8d4c-8fff3552f251",
              "TopicArn": "arn:aws:sns:us-west-2:430636640134:watcher-ai-NoticeReady-0MS3urkThRsY",
              "Subject": "test",
              "Message": "{\"DocID\": \"f17e4d77-9c4b-44dd-9a5a-5819dc86d386\", \"DocName\": \"\\u0e1b\\u0e23\\u0e30\\u0e01\\u0e32\\u0e28\\u0e01\\u0e23\\u0e30\\u0e17\\u0e23\\u0e27\\u0e07\\u0e2d\\u0e38\\u0e15\\u0e2a\\u0e32\\u0e2b\\u0e01\\u0e23\\u0e23\\u0e21  \\u0e40\\u0e23\\u0e37\\u0e48\\u0e2d\\u0e07 \\u0e01\\u0e32\\u0e23\\u0e08\\u0e31\\u0e14\\u0e01\\u0e32\\u0e23\\u0e2a\\u0e34\\u0e48\\u0e07\\u0e1b\\u0e0f\\u0e34\\u0e01\\u0e39\\u0e25\\u0e2b\\u0e23\\u0e37\\u0e2d\\u0e27\\u0e31\\u0e2a\\u0e14\\u0e38\\u0e17\\u0e35\\u0e48\\u0e44\\u0e21\\u0e48\\u0e43\\u0e0a\\u0e49\\u0e41\\u0e25\\u0e49\\u0e27 (\\u0e09\\u0e1a\\u0e31\\u0e1a\\u0e17\\u0e35\\u0e48 2) \\u0e1e.\\u0e28. 2566\"}",
              "Timestamp": "2023-10-05T10:56:18.656Z",
              "SignatureVersion": "1",
              "Signature": "mqu3Kq1wMo5g2+J0iLTiNXggIJGYB9ujCSdyFjRCVQ7KWaN717Fob8vmkFqbOzBwGEvxhv5Wr9WoGPXjJw2OVKcPk9IN8S/IBksyYgs0ifoXBB+SRCU+gCuC1vjEIAt/pv6PtRU6c5Ys5OHxRAU31aJjxcUe9qmx6WR9ApfLblzZ9dqEnXX9LkIpPkpWeJSWvClVUs4f3jVvvpsB9eEKGN/BeYw8Z8V1D4kfEo1jyo/tTYKDR3kLI6YjeVdbuciM4X0hAmvsSXDKCgIxZnW3t4NkhpqpTf8fdnSULtqTKhwPHynWkYyORIjjcinEUfRqP5EO+stHsE9f9e1vlAjxpw==",
              "SigningCertUrl": "https://sns.us-west-2.amazonaws.com/SimpleNotificationService-01d088a6f77103d0fe307c0069e40ed6.pem",
              "UnsubscribeUrl": "https://sns.us-west-2.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-west-2:430636640134:watcher-ai-NoticeReady-0MS3urkThRsY:4a437c1f-63bc-452a-aa95-d4a3e7eee928",
              "MessageAttributes": {}
          }
      }
  ]
}

body = {
    "DocID": "347d7376-bbf3-4130-b8c6-bdd5c505e341",
    "DocName": "ประกาศกระทรวงอุตสาหกรรม ฉบับที่ 7109 (พ.ศ. 2566) ออกตามความในพระราชบัญญัติมาตรฐานผลิตภัณฑ์อุตสาหกรรม พ.ศ. 2511 เรื่อง กำหนดมาตรฐานผลิตภัณฑ์อุตสาหกรรม สิ่งทอ - การวิเคราะห์ทางเคมีเชิงปริมาณ เล่ม 2"
}

event['Records'][0]['Sns']['Message'] = json.dumps(body)
print(event)