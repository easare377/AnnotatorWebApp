from ..controller import *
from ..decorators.route import route
import runpod
import os
import requests


@route('test-runpod')
class TestRunpodController(Controller):

    def process_post_request(self, request_object):
        #17.18
        runpod.api_key = "08BKGQXTXCQW8E51IDIQOO74EY3YRBQEYL3FTURU"
        input_payload = {"input":
            {
                "image_url": "https://uf-ecl-annotator-bucket.s3.us-east-2.amazonaws.com/03f3a4de-cb28-4b04-931b-fc2c206b0887.png"
            }
        }
        try:
            endpoint = runpod.Endpoint("a88wccan78n79h")
            output = endpoint.run_sync(input_payload, timeout=120)
        except Exception as e:
            output = e
            print(e)
        return ok(output)

# def start_pod(api_key, pod_id):
#     url = f'https://api.runpod.io/v1/pods/{pod_id}/start'
#     headers = {
#         'Authorization': f'Bearer {api_key}',
#         'Content-Type': 'application/json'
#     }
#     response = requests.post(url, headers=headers)
#     return response
