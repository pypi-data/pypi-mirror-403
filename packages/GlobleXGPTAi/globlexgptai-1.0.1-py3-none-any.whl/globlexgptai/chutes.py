import requests

class ChutesProvider:
    """Chutes AI Provider for GlobleXGPTAi"""
    def __init__(self, api_key, model="chutes/deepseek-ai/DeepSeek-V3"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.chutes.ai/v1/chat/completions"

    def chat(self, prompt, system_instruction=None):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages
        }
        
        response = requests.post(self.base_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
