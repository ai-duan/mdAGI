"""LLM 客户端"""
import json
import requests
from typing import List, Dict, Any


class LLMClient:
    """LLM 接口封装"""
    
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:3000",
        model: str = "qwen/qwen3-vl-4b"
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_url = f"{self.base_url}/v1/chat/completions"
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict] = None,
        temperature: float = 0.1,
        max_tokens: int = 1024
    ) -> Dict[str, Any]:
        """发送聊天请求"""
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        
        try:
            response = requests.post(
                self.api_url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload),
                timeout=600,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[LLM Error] {e}")
            return None
    
    def summarize(self, text: str, max_length: int = 100) -> str:
        """生成摘要"""
        messages = [
            {"role": "system", "content": "你是摘要专家。生成简洁的摘要。"},
            {"role": "user", "content": f"请用{max_length}字以内总结：\n{text}"}
        ]
        
        result = self.chat(messages, max_tokens=max_length)
        if result:
            return result["choices"][0]["message"]["content"].strip()[:max_length]
        return text[:max_length]
