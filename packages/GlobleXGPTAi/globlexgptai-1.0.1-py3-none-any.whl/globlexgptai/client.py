import requests
import json

class GlobleXGPTAiClient:
    """
    GlobleXGPTAi Python Client Library
    Developed by Himanshu
    """
    def __init__(self, api_key=None, model="globle-1", base_url="https://api.chutes.ai/v1/chat/completions"):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url

    def generate(self, prompt, system_instruction=None):
        """
        Generate a response from GlobleXGPTAi
        """
        if not self.api_key:
            raise ValueError("API Key is required to use GlobleXGPTAiClient")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        if system_instruction is None:
            system_instruction = (
                "You are GlobleXGPTAi, an advanced AI model developed by Himanshu. "
                "Your personality is highly professional, helpful, and creative. "
                "You excel at complex reasoning, coding, and creative writing."
            )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ]
        }

        try:
            response = requests.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content']
        except Exception as e:
            return f"Error: {str(e)}"

    def __repr__(self):
        return f"<GlobleXGPTAiClient(model='{self.model}')>"
