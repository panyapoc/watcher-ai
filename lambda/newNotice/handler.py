import json
import sampleDoc
import watchlist
import boto3
import os
import datetime

#enviroment variables
TABLENAME = os.environ['NOTICERESULT_TABLE_NAME']

#init client
bedrock = boto3.client('bedrock-runtime')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(TABLENAME)

def handler(event, context):
    print(json.dumps(event))
    for record in event['Records']:
        SNSMessage = json.loads(record['Sns']['Message'])
        p[]
        # DocID = SNSMessage['DocID']
        DocID = 0

        DOC = getChunk(DocID)
        WATCHLIST = watchlist()

        # print('DOC ',DOC)
        # print('WATCHLIST ',WATCHLIST)

        respose = queryLLM(DOC)

        respose_body = respose['body'].read().decode('utf-8')

        print('queryLLM ',respose_body)



        writeResult('1',respose_body)

        return json.dumps(respose_body)


def getChunk(docID) :
    doc = sampleDoc(docID)
    return doc

# Fuction to write json to dynamodb table
def writeResult(DocID,output) :
    item = {
        'DocID' : DocID,
        'timestamp' : getTimestampStr(),
        'output' : json.dumps(output)
    }

    respose = table.put_item(Item=item)
    return respose

def getTimestampStr() :
    now = datetime.datetime.now()
    timestamp = now.timestamp()
    return str(timestamp)

print(getChunk(0))

def queryLLM(report):
    # prompt_template = "\n\nHuman:<prompt>\n\nAssistant:"

    prompt_template ="""

Human: <report>{{report}}</report>

<list>
1. เกี่ยวข้องหรือไม่
2. สรุปสาระสำคัญ
3. วันที่มีผลบังคับใช้
4. หน้าที่ที่ต้องปฏิบัติ
5. ประเภทโรงงาน 
6. พรบ. ที่เกี่ยวข้อง ถ้า"มี" ให้ระบุชื่อของพรบ. ที่เกี่ยวข้อง แต่ถ้า"ไม่มี" ให้ตอบว่า ไม่พบพรบ. ที่เกี่ยวข้อง
</list>

<condition>
Yes
</condition>

จาก report ข้างต้น จงสรุปตาม list ให้ด้วยโดยละเอียดตามแต่ละหัวข้อ หาก condition เท่ากับ Yes ให้ตอบว่า "ใช่"ให้อธิบายโดยละเอียด แต่ถ้าหาก condition ไม่ใช่ Yes ให้ตอบว่า "ไม่เกี่ยวข้อง"


Assistant:
"""

    # replace <prompt> with query
    prompt = prompt_template.replace("{{report}}", report)

    body = {
        "prompt": prompt,
        "max_tokens_to_sample": 2048,
        "temperature": 1,
        "top_k": 250,
        "top_p": 0.999,
        "stop_sequences": ["\n\nHuman:"],
        "anthropic_version": "bedrock-2023-05-31"
    }


    response = bedrock.invoke_model(
        accept='*/*',
        body=json.dumps(body),
        contentType='application/json',
        modelId='anthropic.claude-v2'
    )   

    return response
