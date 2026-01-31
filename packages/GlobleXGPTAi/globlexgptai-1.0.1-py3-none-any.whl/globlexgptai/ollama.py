import requests

class OllamaProvider:
    """Ollama Global Provider for GlobleXGPTAi"""
    def __init__(self, api_key, model="deepseek-v3.1:671b-cloud"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://ollama.com/api/chat"

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
            "messages": messages,
            "stream": False
        }
        
        response = requests.post(self.base_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()['message']['content']
