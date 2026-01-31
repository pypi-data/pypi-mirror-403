from contipay.core.client import ContipayClient


class Card:
    PROVIDERS = {
        "visa": {
            "name": "Visa",
            "code": "VA",
        },
        "mastercard": {
            "name": "MasterCard",
            "code": "MA",
        },
    }

    def __init__(self, api_key: str, api_secret: str, mode: str = "dev"):
        self.client = ContipayClient(api_key, api_secret, mode)
        self.method = "direct"
        self.callback_url = None
        self.success_url = None
        self.error_url = None

    def set_urls(self, callback: str, success: str, error: str):
        self.callback_url = callback
        self.success_url = success
        self.error_url = error
        return self

    def pay(self, provider: str, data: dict):
        # 🔍 Validate provider
        config = self.PROVIDERS.get(provider.lower())
        if not config:
            raise ValueError(f"Provider '{provider}' not supported")

        # 🔍 Validate payload structure
        if "transaction" not in data:
            raise ValueError("Missing 'transaction' object")

        if "accountDetails" not in data:
            raise ValueError("Missing 'accountDetails' object")

        if "customer" not in data:
            raise ValueError("Missing 'customer' object")

        # 🔍 Minimal required transaction fields
        required_tx = [
            "amount",
            "currencyCode",
            "merchantId",
            "reference",
        ]

        for field in required_tx:
            if field not in data["transaction"]:
                raise ValueError(f"Missing transaction field: {field}")

        # 🔐 Attach URLs only if set
        if self.callback_url:
            data["callbackUrl"] = self.callback_url
        if self.success_url:
            data["successUrl"] = self.success_url
        if self.error_url:
            data["errorUrl"] = self.error_url

        # 🚀 Send payload AS-IS (important for auth consistency)
        return self.client.post("/acquire/payment", data)
