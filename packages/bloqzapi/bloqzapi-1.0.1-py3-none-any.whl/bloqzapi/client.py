import time
import requests


class BloqzClient:
    def __init__(self, base_url="http://localhost:4000", api_key=None, timeout=30, max_retries=2):
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries

    def _request(self, path, payload):
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        attempt = 0
        while True:
            attempt += 1
            response = requests.post(
                f"{self.base_url}{path}",
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            if response.status_code >= 500 and attempt <= self.max_retries:
                time.sleep(0.3 * attempt)
                continue
            if response.status_code >= 400:
                try:
                    data = response.json()
                except Exception:
                    data = {}
                message = data.get("error", f"Request failed ({response.status_code})")
                raise RuntimeError(message)
            return response.json()

    def parse_intent(self, payload):
        return self._request("/v1/intents/parse", payload)

    def build_plan(self, payload):
        return self._request("/v1/plans/build", payload)

    def simulate_plan(self, payload):
        return self._request("/v1/plans/simulate", payload)

    def validate_plan(self, payload):
        return self._request("/v1/plans/validate", payload)

    def verify_plan(self, payload):
        return self._request("/v1/plans/verify", payload)

