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

def send_response(status:int, body:str):
    return {
        "headers": {
            "Content-Type": "application/json"
        },
        'statusCode': status,
        'body': body
    }

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
    body = json.loads(event['body'])

    feedback = body.get('feedback')

    selections:list = body.get('selections')
    concated_selections = " - ".join(selections)

    token_result = decode_jwt(token)
    if not token_result['is_valid']:
        return send_response(401, f"Nao autorizado {token_result['data']}")
    
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
            return send_response(400, 'Feedback ja enviado!')

        page_id = ej['id']

        properties = {
            'Lead Status': {'status': {'name': status}},
            'Feedback': {
                'rich_text': [{'type': 'text', 'text': {'content': feedback or ''}}]
            },
            'Selections': {
                'rich_text': [{'type': 'text', 'text': {'content': concated_selections or ''}}]
            },
        }
        notion.pages.update(page_id=page_id, properties=properties)

        return send_response(200, "Atualizado com sucesso")
    except Exception as e:
        print(e)
        return send_response(500, 'Error updating lead status')

## SIMPLE OBJECT
# if __name__ == '__main__':
#     token = create_jwt({'lead_id':696})
#     print(f"\n {token} \n")
    # req = {
    #     "resource": "/update",
    #     "path": "/update",
    #     "httpMethod": "POST",
    #     "headers": {
    #         "Content-Type": "application/json"
    #     },
    #     "queryStringParameters": {
    #         "token": token,
    #         "status": "Accept"
    #     },
    #     "body": "{ \"feedback\": \"Meu teste feito aqui\", \"selections\": [\"Item 1\", \"Item 2\"] }",
    #     "isBase64Encoded": False
    # }
    # print(update_lead_status(req, {'isLocal': True}))

