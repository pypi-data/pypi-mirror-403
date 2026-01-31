from .client import GlobleXGPTAiClient
import sys

def main():
    print("GlobleXGPTAi CLI Tool")
    print("Developed by Himanshu")
    
    if len(sys.argv) < 3:
        print("\nUsage: python -m globlexgptai <API_KEY> <PROMPT>")
        return

    api_key = sys.argv[1]
    prompt = " ".join(sys.argv[2:])
    
    client = GlobleXGPTAiClient(api_key=api_key)
    print("\nGenerating response...")
    response = client.generate(prompt)
    print(f"\nResponse: {response}")

if __name__ == "__main__":
    main()
