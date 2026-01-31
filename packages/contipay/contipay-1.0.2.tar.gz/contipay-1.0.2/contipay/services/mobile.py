from contipay.core.client import ContipayClient


class Mobile:
    PROVIDERS = {
        "ecocash": {
            "name": "EcoCash",
            "code": "EC",
        },
        "onemoney": {
            "name": "OneMoney",
            "code": "OM",
        },
        "telecash": {
            "name": "TeleCash",
            "code": "TC",
        },
    }

    def __init__(self, api_key: str, api_secret: str, mode: str = "dev"):
        self.client = ContipayClient(api_key, api_secret, mode)
        self.method = "push"
        self.callback_url = None

    def set_callback(self, callback: str):
        self.callback_url = callback
        return self

    def pay(self, provider: str, data: dict):
        # 🔍 Validate provider
        config = self.PROVIDERS.get(provider.lower())
        if not config:
            raise ValueError(f"Provider '{provider}' not supported")

        # 🔍 Validate payload structure (MATCHES CARD)
        if "transaction" not in data:
            raise ValueError("Missing 'transaction' object")

        if "accountDetails" not in data:
            raise ValueError("Missing 'accountDetails' object")

        if "customer" not in data:
            raise ValueError("Missing 'customer' object")

        # 🔍 Minimal transaction validation
        required_tx = [
            "amount",
            "currencyCode",
            "merchantId",
            "reference",
        ]

        for field in required_tx:
            if field not in data["transaction"]:
                raise ValueError(f"Missing transaction field: {field}")

        # 🔐 Attach callback if set
        if self.callback_url:
            data["callbackUrl"] = self.callback_url

        # 🚀 Send payload AS-IS (NO PayloadGenerator)
        return self.client.post("/acquire/payment", data)
