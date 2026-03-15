import os

from dotenv import load_dotenv
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI")
NEURO_SYMBOLIC_DIR = "/Users/euzhengxi/dev/swe_practices/llm/neuro_symbolic/problems"


if __name__ == "__main__":
    problems = []
    for file in os.listdir(NEURO_SYMBOLIC_DIR):
        filepath = f"{NEURO_SYMBOLIC_DIR}/{file}"
        with open(filepath, "r") as f:
            problems.append(f.read())

    #pipeline for generating states

    
    
    