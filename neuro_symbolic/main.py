import os
from openai import OpenAI
from dotenv import load_dotenv

NEURO_SYMBOLIC_DIR = "/Users/euzhengxi/dev/swe_practices/llm/neuro_symbolic/problems"
DOMAIN = ""
DESC1, PDDL1 = "", ""
DESC2, PDDL1 = "", ""

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI")
client = OpenAI(api_key=OPENAI_API_KEY)

if __name__ == "__main__":
    #reading in files for system prompt
    with open("./PDDL/domain.pddl", "r") as file:
        DOMAIN = file.read()

    with open("./PDDL/pb01.pddl", "r") as file:
        PDDL1 = PDDL2 = file.read()
    
    with open("./problems/pb01.txt", "r") as file:
        DESC1 = file.read()
    
    with open("./problems/pb02.txt", "r") as file:
        DESC2 = file.read()
    
    SYSTEM_PROMPT = f"You are generating the initial and goal state for the blocksworld problem for a classical solver based on a short description. \
                    Ensure the output is in PDDL format.The following are a few examples: \n \
                    Example 1: \n\
                    - description: {DESC1} \n\ 
                    - output: {PDDL1} \n\
                    \n\
                    Example 2: \n\
                    - description: {DESC2} \n\
                    - output: {PDDL2}"
    
    #loading in problem descriptions
    problems = []
    for file in os.listdir(NEURO_SYMBOLIC_DIR):
        filepath = f"{NEURO_SYMBOLIC_DIR}/{file}"
        with open(filepath, "r") as f:
            problems.append(f.read())
    
    for desc in problems:
        user_content = f"actual description: {desc} \n\
                    output: <YOUR_OUTPUT>"
        
        response = client.responses.create(
            model="gpt-4o",
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ]
        )

        print(response.output_text)
    
    
    
    
    