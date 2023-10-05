import json
import sampleDoc
import watchlist
import boto3
import os
import datetime
import re

#enviroment variables
TABLENAME = os.environ['NOTICERESULT_TABLE_NAME']

#init client
bedrock = boto3.client('bedrock-runtime')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(TABLENAME)

def handler(event, context):
    # print(json.dumps(event))
    for record in event['Records']:
        print('@@@@@@@@@@@@@@@DocID@@@@@@@@@@@@@@@')
        
        DocID = record['Sns']['Message']
        # DocID = 0

        DOC = getChunk(0)
        WATCHLIST = watchlist()

        # print('DOC ',DOC)
        # print('WATCHLIST ',WATCHLIST)

        respose = queryLLM(DOC)

        respose_body = respose['body'].read().decode('utf-8')

        print("DOC LEN ", len(respose_body))

        print('queryLLM ',respose_body)
        print('parsed', parseLLM(str(respose_body)))

        writeResult('2',parseLLM(respose_body))

        return json.dumps(respose_body)


def getChunk(docID) :
    doc = sampleDoc(docID)
    return doc

# Fuction to write json to dynamodb table
def writeResult(DocID,output) :
    item = {
        'DocID' : DocID,
        'timestamp' : getTimestampStr(),
        'output' : output
    }

    respose = table.put_item(Item=item)
    return respose

def getTimestampStr() :
    now = datetime.datetime.now()
    timestamp = now.timestamp()
    return str(timestamp)

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
6. พรบ. ที่เกี่ยวข้อง
</list>

<condition>
- เพิ่ม $$ ก่อนเริ่มแต่ละข้อใน list
- ใส่เลขหัวข้อใน list
- ใส่ @@ หลังคำตอบแต่ละข้อใน list
</condition>

จาก report ให้สรุปตาม list โดยละเอียด แยกเป็นหัวข้อ 
หาก list = Yes ตอบว่า "ใช่" และอธิบาย แต่ถ้าหาก = No ตอบว่า "ไม่เกี่ยวข้อง"

ผลลัพท์ list ให้ใส่ cut ตามเงื่อนไขใน condition

คำตอบข้อที่ 6 จาก list หา พ.ร.บ. ที่เกี่ยวข้องกับ พ.ร.บ. ที่ประกาศก่อนหน้าให้ด้วย

Assistant:
"""

    # replace <prompt> with query
    prompt = prompt_template.replace("{{report}}", report)

    print('Prompt len ', len(prompt))

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

def parseLLM(llm_output) :
    output_table = []
    matches = re.findall(r'\$\$(.*?)@@', llm_output)

    for match in matches:
        output_table.append(match)

    return output_table