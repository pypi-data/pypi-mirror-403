import requests
import base64

class ContipayClient:
    def __init__(self, api_key, api_secret, mode="dev"):
        self.api_key = api_key
        self.api_secret = api_secret
        self.mode = mode
        self.base_url = (
            "https://api-uat.contipay.net"
            if mode == "dev"
            else "https://api.contipay.net"
        )

    def _headers(self):
        token = base64.b64encode(
            f"{self.api_key}:{self.api_secret}".encode()
        ).decode()

        return {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json"
        }

    def post(self, endpoint, payload):
        response = requests.post(
            self.base_url + endpoint,
            json=payload,
            headers=self._headers(),
            timeout=30
        )
        return response.json()
