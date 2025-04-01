import json
from notion_client import Client
from dotenv import load_dotenv
import os
import jwt
from datetime import datetime, timedelta, UTC


load_dotenv()

LEADS_NOTION_KEY = os.getenv('LEADS_NOTION_KEY')
LEADS_DATABASE_ID = os.getenv('LEADS_DATABASE_ID')
ALGORITHM = os.getenv('JWT_ALGORITHM')
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')


def create_jwt(payload: dict):
    return jwt.encode(
        {**payload, "exp": int((datetime.now(UTC) + timedelta(days=60)).timestamp())},
        algorithm=ALGORITHM,
        key=JWT_SECRET_KEY,
    )

def decode_jwt(token: str):
    try:
        decoded = jwt.decode(token, key=JWT_SECRET_KEY, algorithms=[ALGORITHM])
        return {
            'is_valid': True,
            'data': decoded
        }
    except Exception as e:
        return {
            'is_valid': False,
            'data': e
        }


def update_lead_status(event, context):
    token = event['queryStringParameters']['token']
    status = event['queryStringParameters']['status']

    token_result = decode_jwt(token)
    if not token_result['is_valid']:
        return {
            'status': 401,
            'body': json.dumps(token_result['data']),
            'message': 'Não autorizado' 
        }
    
    payload = token_result['data']
    lead_id = int(payload['lead_id'])

    notion = Client(auth=LEADS_NOTION_KEY)

    try:
        database_id = LEADS_DATABASE_ID

        query = {
            'database_id':database_id,
            'filter': {'and':[{'property': 'ID','unique_id': {'equals': lead_id}}]}
        }
        registrers = notion.databases.query(**query)

        ej = registrers['results'][0]

        current_status = ej['properties']['Lead Status']['status']['name']
        if current_status == 'Refused' or current_status == 'Accept':
            return {
                'status': 400,
                'body': json.dumps('Feedback já enviado!'),
                'message': 'Feedback já enviado!'
            }

        page_id = ej['id']

        notion.pages.update(page_id=page_id, properties={'Lead Status': {'status': {'name': status}}})

        return {
            'statusCode': 200,
            'body': json.dumps('Lead status updated successfully'),
            'message': "Atualizado com sucesso"
        }
    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'body': json.dumps('Error updating lead status'),
            'message': 'Error updating lead status'
        }




# if __name__ == "__main__":
    # token = create_jwt({"lead_id": 696})
    # print("\n\n")
    # print(token)
    # print("\n\n")

    # print(decode_jwt(token))

    # request ={
    #     "resource": "/",
    #     "path": "/",
    #     "httpMethod": "GET",
    #     "headers": {
    #         "Accept": "application/json",
    #         "Host": "example.execute-api.us-east-1.amazonaws.com",
    #         "User-Agent": "PostmanRuntime/7.28.4"
    #     },
    #     "queryStringParameters": {
    #         "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsZWFkX2lkIjo2OTYsImV4cCI6MTc0ODY1MzI4Nn0.gqzWWFfVPZFVdpdoA1dysjgV8RjhJinroSUW6quvan8",
    #         "status": "Accept"
    #     },
    #     "pathParameters": None,
    #     "stageVariables": None,
    #     "requestContext": {
    #         "resourceId": "abcdef",
    #         "resourcePath": "/minharecurso",
    #         "httpMethod": "GET",
    #         "requestId": "1234-5678-91011",
    #         "accountId": "123456789012",
    #         "stage": "prod",
    #         "identity": {
    #         "sourceIp": "127.0.0.1",
    #         "userAgent": "PostmanRuntime/7.28.4"
    #         },
    #         "apiId": "api-id"
    #     },
    #     "body": None,
    #     "isBase64Encoded": False
    # }
    # resp = update_lead_status(request, {"local":True})
    # print(resp)

