import requests

from pilot.config.config_reader import get_config
from pilot.logging.logger import get_logger


class AIClient:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.config_dto = get_config()
        self.headers = {"Content-Type": "application/json;charset=utf-8"}

    def call(self, user_prompt: str, system_prompt: str = "") -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        request_data = self._build_request_payload(messages)

        response_data = self._send_post_request(self.api_url, self.headers, request_data)
        if not isinstance(response_data, dict):
            self.logger.error("無効なAPI応答またはリクエスト失敗")
            return ""

        result_text = self._extract_response_content(response_data)
        return result_text

    def _build_request_payload(self, messages: list[dict]) -> dict:
        raise NotImplementedError("サブクラスでリクエストペイロードの構築を実装してください")

    def _send_post_request(self, url: str, headers: dict, data: dict) -> dict or str:
        try:
            response = requests.post(url, headers=headers, json=data)
        except Exception as e:
            self.logger.error(f"リクエスト失敗: {e}")
            return ""
        if response.status_code != 200:
            self.logger.error(f"ステータスコード {response.status_code}: {response.text}")
            return ""
        try:
            return response.json()
        except Exception as e:
            self.logger.error(f"JSON解析失敗: {e}")
            return ""

    def _extract_response_content(self, response: dict) -> str:
        raise NotImplementedError("サブクラスでレスポンスの解析を実装してください")


class LMStudioClient(AIClient):
    def __init__(self):
        super().__init__()
        self.api_url = self.config_dto.lm_studio_api_url
        self.model_name = self.config_dto.lm_studio_model_name

    def _build_request_payload(self, messages: list[dict]) -> dict:
        payload = {
            "model": self.model_name,
            "stream": False,
            "temperature": 0.8,
            "max_tokens": 15000,
            "messages": messages,
        }
        return payload

    def _extract_response_content(self, response: dict) -> str:
        if not isinstance(response, dict):
            return str(response)
        if "usage" in response:
            self.logger.debug(f"使用状況: {response['usage']}")
        choices = response.get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content") or str(response)
        return str(response)
