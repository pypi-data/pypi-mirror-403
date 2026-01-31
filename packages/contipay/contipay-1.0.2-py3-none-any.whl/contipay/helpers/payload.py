class PayloadGenerator:

    @staticmethod
    def card(provider, code, data):
        payload = data.copy()
        payload["provider"] = provider
        payload["providerCode"] = code
        return payload

    @staticmethod
    def mobile(provider, code, data):
        payload = data.copy()
        payload["provider"] = provider
        payload["providerCode"] = code
        return payload
