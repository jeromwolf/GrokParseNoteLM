import subprocess

pdf_path = "Data/pdftest.pdf"
tests = [
    {
        "name": "Upstage",
        "cmd": ["python", "main.py", pdf_path, "--model", "upstage", "--output-dir", "output/upstage_test"]
    },
    {
        "name": "Llama",
        "cmd": ["python", "main.py", pdf_path, "--model", "llama", "--model-name", "llama3:latest", "--output-dir", "output/llama_test"]
    },
    {
        "name": "OpenAI",
        "cmd": ["python", "main.py", pdf_path, "--model", "openai", "--model-name", "gpt-4-turbo-preview", "--output-dir", "output/openai_test"]
    },
    {
        "name": "Gemini",
        "cmd": ["python", "main.py", pdf_path, "--model", "gemini", "--model-name", "gemini-pro", "--output-dir", "output/gemini_test"]
    }
]

for test in tests:
    print(f"\n===== {test['name']} 테스트 시작 =====")
    result = subprocess.run(test["cmd"])
    if result.returncode == 0:
        print(f"===== {test['name']} 완료 =====")
    else:
        print(f"===== {test['name']} 실패 (코드: {result.returncode}) =====")
