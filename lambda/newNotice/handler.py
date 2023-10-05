import json
import sampleDoc
import watchlist
import boto3
import os
import datetime
import re
import requests as request;

# # # unit test
# import dotenv
# dotenv.load_dotenv()

#enviroment variables
TABLENAME = os.environ['NOTICERESULT_TABLE_NAME']

#init client
bedrock = boto3.client('bedrock-runtime')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(TABLENAME)

def handler(event, context):
    for record in event['Records']:
        # print(record['Sns']['Message'])
        message = record['Sns']['Message']
        
        message_json = json.loads(message)

        DocID = message_json['DocID']
        DocName = message_json['DocName']

        print('DocID:',DocID)
        print('DocName:',DocName)
        # DocID = 0
        # DocName = 'ประกาศกระทรวงอุตสาหกรรม ฉบับที่'

        # !!!CHANGE THIS Get DOC
        FULL_DOC = getDoc(DocID)

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

            ref_docs = classification_result['related']

            print('------ASKING LLM FOR OUTPUT---------')
            # Get related data for LLM
            
            related_doc = getRelatedChunk(DocName,ref_docs,WATCHLIST)
            output = queryLLMforoutput(related_doc,watchlist_string)

            print('------queryLLMforoutput---------')
            print(output)

            writeResult(DocID,output)


        else :
            print("This Doc not related")
            writeResult(DocID,"NOT RELATED")



        return 0

def getDoc(index) :
    # doc = sampleDoc(index)
    print(index)

    stage = "prod"
    url = 'https://ahtrxccf3d.execute-api.us-east-1.amazonaws.com/'+stage+'/get-full-doc'
    body = {
        "docID": index
    }
    reponse = httpGET(url, body)
    output = reponse.text
    print(output)
    response_json  = json.loads(output)

    text = response_json['body']

    print('Full Doc',text)
    return text

def getRelatedChunk(docname,relateddoc_array,watchlist_array) :
    related_chunk = {}
    relateddoc_array.append(docname)
    for watchitem in watchlist_array:
        stage = "prod"
        url = 'https://ahtrxccf3d.execute-api.us-east-1.amazonaws.com/'+stage+'/query-word'
        body = {
            "text": watchitem,
            "sourceList": relateddoc_array
        }
        print(body)
        reponse = httpGET(url, body)
        output = reponse.text
        print(output)
        mydict = json.loads(output)

        for result in mydict['body'] : 
            # print(result)
            if (result['score'] > 0.5) :
                print(result['score'], ' ', result['text'])
                related_chunk[result['chunkID']] = result['text']


    print('related_chunk',related_chunk)

    LLMinput = ''
    for key,value in related_chunk:
        LLMinput = LLMinput + value

    return LLMinput

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

def queryLLMforoutput(report,watchlist_string):
    # prompt_template = "\n\nHuman:<prompt>\n\nAssistant:"

    prompt_template ="""

Human: <report>{{report}}</report>

<list>
1. สรุปสาระสำคัญโดยละเอียด
2. วันที่มีผลบังคับใช้
3. สิ่งที่ทำ ให้ตอบเป็นข้อๆ
4. ใน report พูดถึงอะไรที่อยู่ใน watchlist บ้าง ให้ตอบเป็นข้อๆ
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
"""

    # replace <prompt> with query
    prompt = prompt_template.replace("{{report}}", report).replace("{{watchlist}}", watchlist_string)

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


# ----------------------------------------
# --------------UNIT TEST ----------------
# ----------------------------------------

# event = {'Records': [{'EventSource': 'aws:sns', 'EventVersion': '1.0', 'EventSubscriptionArn': 'arn:aws:sns:us-west-2:430636640134:watcher-ai-NoticeReady-0MS3urkThRsY:4a437c1f-63bc-452a-aa95-d4a3e7eee928', 'Sns': {'Type': 'Notification', 'MessageId': 'be73d267-adc0-5c63-8d4c-8fff3552f251', 'TopicArn': 'arn:aws:sns:us-west-2:430636640134:watcher-ai-NoticeReady-0MS3urkThRsY', 'Subject': 'test', 'Message': '{"DocID": "347d7376-bbf3-4130-b8c6-bdd5c505e341", "DocName": "\\u0e1b\\u0e23\\u0e30\\u0e01\\u0e32\\u0e28\\u0e01\\u0e23\\u0e30\\u0e17\\u0e23\\u0e27\\u0e07\\u0e2d\\u0e38\\u0e15\\u0e2a\\u0e32\\u0e2b\\u0e01\\u0e23\\u0e23\\u0e21 \\u0e09\\u0e1a\\u0e31\\u0e1a\\u0e17\\u0e35\\u0e48 7109 (\\u0e1e.\\u0e28. 2566) \\u0e2d\\u0e2d\\u0e01\\u0e15\\u0e32\\u0e21\\u0e04\\u0e27\\u0e32\\u0e21\\u0e43\\u0e19\\u0e1e\\u0e23\\u0e30\\u0e23\\u0e32\\u0e0a\\u0e1a\\u0e31\\u0e0d\\u0e0d\\u0e31\\u0e15\\u0e34\\u0e21\\u0e32\\u0e15\\u0e23\\u0e10\\u0e32\\u0e19\\u0e1c\\u0e25\\u0e34\\u0e15\\u0e20\\u0e31\\u0e13\\u0e11\\u0e4c\\u0e2d\\u0e38\\u0e15\\u0e2a\\u0e32\\u0e2b\\u0e01\\u0e23\\u0e23\\u0e21 \\u0e1e.\\u0e28. 2511 \\u0e40\\u0e23\\u0e37\\u0e48\\u0e2d\\u0e07 \\u0e01\\u0e33\\u0e2b\\u0e19\\u0e14\\u0e21\\u0e32\\u0e15\\u0e23\\u0e10\\u0e32\\u0e19\\u0e1c\\u0e25\\u0e34\\u0e15\\u0e20\\u0e31\\u0e13\\u0e11\\u0e4c\\u0e2d\\u0e38\\u0e15\\u0e2a\\u0e32\\u0e2b\\u0e01\\u0e23\\u0e23\\u0e21 \\u0e2a\\u0e34\\u0e48\\u0e07\\u0e17\\u0e2d - \\u0e01\\u0e32\\u0e23\\u0e27\\u0e34\\u0e40\\u0e04\\u0e23\\u0e32\\u0e30\\u0e2b\\u0e4c\\u0e17\\u0e32\\u0e07\\u0e40\\u0e04\\u0e21\\u0e35\\u0e40\\u0e0a\\u0e34\\u0e07\\u0e1b\\u0e23\\u0e34\\u0e21\\u0e32\\u0e13 \\u0e40\\u0e25\\u0e48\\u0e21 2"}', 'Timestamp': '2023-10-05T10:56:18.656Z', 'SignatureVersion': '1', 'Signature': 'mqu3Kq1wMo5g2+J0iLTiNXggIJGYB9ujCSdyFjRCVQ7KWaN717Fob8vmkFqbOzBwGEvxhv5Wr9WoGPXjJw2OVKcPk9IN8S/IBksyYgs0ifoXBB+SRCU+gCuC1vjEIAt/pv6PtRU6c5Ys5OHxRAU31aJjxcUe9qmx6WR9ApfLblzZ9dqEnXX9LkIpPkpWeJSWvClVUs4f3jVvvpsB9eEKGN/BeYw8Z8V1D4kfEo1jyo/tTYKDR3kLI6YjeVdbuciM4X0hAmvsSXDKCgIxZnW3t4NkhpqpTf8fdnSULtqTKhwPHynWkYyORIjjcinEUfRqP5EO+stHsE9f9e1vlAjxpw==', 'SigningCertUrl': 'https://sns.us-west-2.amazonaws.com/SimpleNotificationService-01d088a6f77103d0fe307c0069e40ed6.pem', 'UnsubscribeUrl': 'https://sns.us-west-2.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-west-2:430636640134:watcher-ai-NoticeReady-0MS3urkThRsY:4a437c1f-63bc-452a-aa95-d4a3e7eee928', 'MessageAttributes': {}}}]}

# handler(event,'test')

# getDoc("47e82e74-3def-43af-99af-85bec95574f1")