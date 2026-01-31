import sys
import requests
import json

def main():
    if len(sys.argv) < 2:
        print("Usage: nemotron-quick "your prompt here"")
        sys.exit(1)

    prompt = " ".join(sys.argv[1:])

    headers = {
        "Authorization": "Bearer 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",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "nvidia/nemotron-nano-12b-v2-vl:free",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    r = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        data=json.dumps(payload)
    )

    r.raise_for_status()

    print(r.json()["choices"][0]["message"]["content"])

if __name__ == "__main__":
    main()
