import threading
from typing import Dict, Any, Optional
import requests

class VertexAISingleton:
    _instance: Optional['VertexAISingleton'] = None
    _lock = threading.Lock()

    def __new__(cls, model_name: str = "openai/gpt-oss-20b"):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(VertexAISingleton, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_name: str = "openai/gpt-oss-20b"):
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    self.model_name = model_name
                    self.base_url = "http://127.0.0.1:3000/v1"

                    #self.encoding = tiktoken.get_encoding("cl100k_base")

                    self._session = requests.Session()

                    self._initialized = True

    def generate_content(self, prompt: str) -> Dict[str, Any]:
        """複数スレッドから安全に呼び出し可能"""
        try:
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }

            resp = self._session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=600
            )
            resp.raise_for_status()
            data = resp.json()

            content = data["choices"][0]["message"]["content"]

            return {
                "prompt": prompt,
                "response": self._remove_code_fence(content),
                "success": True,
                "error": None
            }

        except Exception as e:
            return {
                "prompt": prompt,
                "response": None,
                "success": False,
                "error": str(e)
            }

    def start_chat(self):
        """
        VertexAI の ChatSession と完全互換は不可能だが、
        既存コードを壊さないために「退化実装」を提供
        """
        return _LMStudioChatSession(self)

    def count_tokens(self, text: str) -> int:
        return 1
        #try:
        #    return len(self.encoding.encode(text))
        #except Exception as e:
        #    print(f"トークン計算失敗: {e}")
        #    return 0

    def _remove_code_fence(self, text: str) -> str:
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines)

    @classmethod
    def get_instance(cls, model_name: str = "openai/gpt-oss-20b") -> 'VertexAISingleton':
        return cls(model_name)

class _LMStudioChatSession:
    """
    VertexAI ChatSession の「最低限互換」
    """
    def __init__(self, client: VertexAISingleton):
        self._client = client
        self._messages = []

    def send_message(self, message: str):
        self._messages.append({"role": "user", "content": message})

        payload = {
            "model": self._client.model_name,
            "messages": self._messages
        }

        resp = self._client._session.post(
            f"{self._client.base_url}/chat/completions",
            json=payload,
            timeout=60
        )
        resp.raise_for_status()
        data = resp.json()

        reply = data["choices"][0]["message"]["content"]
        self._messages.append({"role": "assistant", "content": reply})

        class _Resp:
            def __init__(self, text):
                self.text = text

        return _Resp(reply)