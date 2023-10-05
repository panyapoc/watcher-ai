import json
import sampleDoc
import watchlist
import boto3
import os
import datetime
import re
import requests as request;

# unit test
import dotenv
dotenv.load_dotenv()

#enviroment variables
TABLENAME = os.environ['NOTICERESULT_TABLE_NAME']

#init client
bedrock = boto3.client('bedrock-runtime')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(TABLENAME)

def handler(event, context):
    # print(json.dumps(event))
    for record in event['Records']:
        
        DocID = record['Sns']['Message']
        # DocID = 0

        # !!!CHANGE THIS Get DOC
        FULL_DOC = getDoc(0)

        # Pasrse Watchlist for LLM
        WATCHLIST = watchlist()
        watchlist_string = ''
        count = 1
        for i,item in enumerate(WATCHLIST):
            if i == (len(WATCHLIST)-1):
                watchlist_string = watchlist_string + str(count)+'. '+ item
            else :
                watchlist_string = watchlist_string + str(count)+'. '+ item + '\n'
            count = count + 1
        

        # Doc classification
        print('------ASKING LLM FOR CLASSIFICATION---------')
        queryLLMforrefResponse = queryLLMforref(FULL_DOC,watchlist_string)
        classification_result = findJSONinString(queryLLMforrefResponse)
        print(classification_result)

        if classification_result['inwatchlist'] == 'true' :
            print("This Doc is related")

            related_doc = classification_result['related']

            print('------ASKING LLM FOR OUTPUT---------')
            # Get related data for LLM
            related_doc = getChunk('docname','relateddoc','seachterm')
            output = queryLLMforoutput(related_doc)

            print('------queryLLMforoutput---------')
            print(output)




        else :
            print("This Doc not related")
            writeResult('NOT_RELATED_DOC',"NOT RELATED")



        return 0

def getDoc(index) :
    doc = sampleDoc(index)
    return doc

def getChunk(docname,relateddoc,seachterm) :

    # seachterm = "พระราชบัญญัติมาตรฐานผลิตภัณฑ์อุตสาหกรรม"
    # sourceList = [docname]
    # sourceList.append(relateddoc)
    # stage = "test"
    # url = 'https://ahtrxccf3d.execute-api.us-east-1.amazonaws.com/'+stage+'/query-word'
    # body = {
    # "text": seachterm,
    # "sourceList": sourceList
    # }
    # reponse = httpGET(url, body)
    # output = reponse.text
    # mydict = json.loads(output)

    # doc = ''

    # for result in mydict['body'] : 
    #     # print(result)
    #     if (result['score'] > 0.5) :
    #         print(result['score'], ' ', result['text'])
    #         doc = doc + '\n\n'+result['text']

    # print('-------LLM INPUT-------')
    # print(doc)

    doc = sampleDoc(0)
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

def queryLLMforref(report,watchlist_string):
    # prompt_template = "\n\nHuman:<prompt>\n\nAssistant:"

    prompt_template ="""

Human: <report>{{report}}</report>

<watchlist>
{{watchlist}}
</watchlist>


<list>
1. มีพูดถถึงของใน watchlist หรือไม่ return in the form below. "inwatchlist": "true/false"
2. หา พรบ. ที่เกี่ยวข้อง และหา "ประกาศ" หรือ "พ.ร.บ" return in the form below. "related": [ array ของเอกสารทีเกี๋ยวข้อง]
</list>

จาก report ตอบคำถามให้ list 
do not return any string but json. return only json in this format

{
    "inwatchlist": "true",
    "related": [ array ของเอกสารทีเกี๋ยวข้อง]
}

Assistant:
"""

    # replace <prompt> with query
    prompt = prompt_template.replace("{{report}}", report).replace("{{watchlist}}", watchlist_string)
    
    # print('@@@@@PROMPT@@@@@')
    # print(prompt)
    print('queryLLMforref prompt len: ', len(prompt))

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

    LLMresponse = json.loads(response['body'].read().decode('utf-8'))
    print('LLMresponse', LLMresponse['completion'])

    return LLMresponse['completion']

def queryLLMforoutput(report):
    # prompt_template = "\n\nHuman:<prompt>\n\nAssistant:"

    prompt_template ="""

Human: <report>{{report}}</report>

<list>
1. Summary: สรุปสาระสำคัญอย่างน้อย 100 คำ
2. Effective Date : วันที่มีผลบังคับใช้ ให้ตอบเป็น dd/mm/YYYY และรายละเอียดอื่นถ้ามี
3. Action item: หน้าที่ที่ต้องปฏิบัติ ให้ตอบเป็นข้อๆ
4. inventory : ใน report พูถึงอะไรใน watchlist บ้าง 
</list>

<watchlist>{{watchlist}}</watchlist>

จาก report ให้ตอบคำถามใน list ตาม condition

<condition>
- ถ้าตอบได้ให้ตอบคำถามโดยละเอียด
- หากตอบไม่ได้ให้ใส่คำตอบเป็น "ข้อมูลไม่เพียงพอ"
- ตอบเป็น json ตาม template
</condition>

<template>
{
    "summary" : "คำตอบข้อที่ 1",
    "effectiveDate" : "คำตอบข้อที่ 2",
    "actionItem" : "คำตอบข้อที่ 3",
    "inventory" : "คำตอบข้อที่ 4"
}
</template>

Assistant:

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

    LLMresponse = json.loads(response['body'].read().decode('utf-8'))
    print('LLMresponse', LLMresponse)
    return LLMresponse['completion']

def parseLLM(llm_output) :
    output_table = []
    matches = re.findall(r'\$\$(.*?)@@', llm_output)

    for match in matches:
        output_table.append(match)

    return output_table


# sent GET request with json body to url
def httpGET(url, body):
    return request.get(url, json=body);

def findJSONinString(stringtofind):
    # Create a custom JSON scanner
    class JSONScanner(json.JSONDecoder):
        def scan_once(self, s, idx):
            try:
                obj, end_idx = super().raw_decode(s, idx)
                return obj, end_idx
            except json.JSONDecodeError:
                raise StopIteration(None, end_idx)

    # Initialize the JSONScanner
    scanner = JSONScanner()

    # Initialize variables to track the largest JSON object and its size
    largest_json_object = None
    largest_json_size = 0

    # Initialize the starting index for scanning
    index = 0

    # Iterate through the multiline string to find and compare JSON objects
    while index < len(stringtofind):
        try:
            obj, end_index = scanner.raw_decode(stringtofind, index)
            
            # Calculate the size of the JSON object (length of the string representation)
            json_size = len(json.dumps(obj))
            
            # Compare the size with the largest found so far
            if json_size > largest_json_size:
                largest_json_object = obj
                largest_json_size = json_size
            
            index = end_index
        except json.JSONDecodeError:
            index += 1

    return largest_json_object


# ------------------------------------------------------------------------------------------------
# UNIT TEST
# ------------------------------------------------------------------------------------------------

event = {
    "Records": [
      {
        "EventSource": "aws:sns",
        "EventVersion": "1.0",
        "EventSubscriptionArn": "arn:aws:sns:us-east-1::ExampleTopic",
        "Sns": {
          "Type": "Notification",
          "MessageId": "95df01b4-ee98-5cb9-9903-4c221d41eb5e",
          "TopicArn": "arn:aws:sns:us-east-1:123456789012:ExampleTopic",
          "Subject": "example subject",
          "Message": "example message",
          "Timestamp": "1970-01-01T00:00:00.000Z",
          "SignatureVersion": "1",
          "Signature": "EXAMPLE",
          "SigningCertUrl": "EXAMPLE",
          "UnsubscribeUrl": "EXAMPLE",
          "MessageAttributes": {
            "Test": {
              "Type": "String",
              "Value": "TestString"
            },
            "TestBinary": {
              "Type": "Binary",
              "Value": "TestBinary"
            }
          }
        }
      }
    ]
  }

handler(event, None)