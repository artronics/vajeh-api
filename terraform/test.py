import json


def lambda_handler(event, context):
    b = {"message": "hello api"}
    return {
        'statusCode': 200,
        'body': json.dumps(b)
    }
