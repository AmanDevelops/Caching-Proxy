import json
from flask import Response
import base64

def serialize_response(response: Response) -> str:
    return json.dumps({
        'status_code': response.status_code,
        'headers': dict(response.headers),
        'data': base64.b64encode(response.get_data()).decode('utf-8')
    })

def deserialize_response(serialized: str) -> Response:
    payload = json.loads(serialized)
    return Response(
        response=base64.b64decode(payload['data']),
        status=payload['status_code'],
        headers=payload['headers']
    )