import base64
import hashlib
import hmac
import random
import time
import urllib

import requests


class CloudStackAPIClient:
    def __init__(self, cloudstack_host, api_key, secret_key):
        self.session = requests.Session()
        self.base_url = "http://" + cloudstack_host + ":8080/client/api?"
        self.api_key = api_key
        self.secret_key = secret_key

    def send_request(self, inputs):
        inputs["response"] = "json"
        inputs["apikey"] = self.api_key
        request_url = "&".join(
            ["=".join([r, urllib.parse.quote(inputs[r])]) for r in inputs.keys()]
        )
        sig_str = "&".join(
            [
                "=".join(
                    [
                        k.lower(),
                        urllib.parse.quote(inputs[k].lower().replace("+", "%20")),
                    ]
                )
                for k in sorted(inputs.keys())
            ]
        )
        sig = urllib.parse.quote(
            base64.encodebytes(
                hmac.new(
                    self.secret_key.encode(), sig_str.encode(), hashlib.sha1
                ).digest()
            ).strip()
        )
        req = self.base_url + request_url + "&signature=" + sig

        response = self.session.get(req)
        return response

    def get_job_status(self, job_id):
        inputs = {"command": "queryAsyncJobResult", "jobid": job_id}
        return self.send_request(inputs).json()

    def wait_for_job(
        self, job_id, max_retries: int = 5, min_sleep: int = 5, max_sleep: int = 10
    ):
        retries = 0
        status = self.get_job_status(job_id).get("jobstatus", 0)
        while status == 0 and retries < max_retries:
            time.sleep(random.randint(min_sleep, max_sleep))
            retries += 1
        return status

    def verify_connection(self, logger):
        inputs = {"command": "listVirtualMachines"}

        logger.info(inputs)
        response = self.send_request(inputs)
        logger.info(response)

        if response.status_code != 200 and response.status_code != 201:
            raise Exception("Cannot connect to CloudStack management server.")

        return True
