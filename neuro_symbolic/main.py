import os
from openai import OpenAI
from dotenv import load_dotenv
import subprocess

PROBLEMS_DIR = "/Users/euzhengxi/dev/swe_practices/llm/neuro_symbolic/problems"
PROBLEM_TYPE = ""
DOMAIN_FILEPATH = ""
PROBLEM_FILELIST = []
PDDL_FILELIST = []

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI")
client = OpenAI(api_key=OPENAI_API_KEY)

def generate_filepaths(problem_type:str, sample_count:int):
    domain_filepath = f"./PDDL/{problem_type}/domain.pddl"

    problem_filelist, pddl_filelist = [], []
    for i in range(sample_count):
        problem_filelist.append(f"./problems/{problem_type}/sample{i + 1}.txt")
        pddl_filelist.append(f"./PDDL/{problem_type}/sample{i + 1}.pddl")

    return domain_filepath, problem_filelist, pddl_filelist 



def generate_system_prompt(problem_type:str, domain_filepath:str, problem_filelist:list, pddl_filelist:list):
    #create template for system prompt - context + domain knowledge
    domain_pddl = ""
    with open(domain_filepath, "r") as file:
        domain_pddl = file.read()
    
    system_prompt = f"You are generating the initial and goal state for the {problem_type} problem for a classical solver based on a short description. \
                    This is the domain pddl: {domain_pddl} \n \
                    Ensure the output is in PDDL format.The following are a few examples: \n\ "
    
    prompt_list = [system_prompt]

    #complement template with a few examples for few shot prompting
    n = len(problem_filelist)
    problem_description, pddl = "", ""
    for i in range(n):
        with open(problem_filelist[i], "r") as f1:
            problem_description = f1.read()
        
        with open(pddl_filelist[i], "r") as f2:
            pddl = f2.read()
        
        example_prompt = f"Example {i + 1}: \n\
                    - description: {problem_description} \n\
                    - output: {pddl} \n\ "
        
        if (i != n - 1):
            example_prompt += "\n \ "

        prompt_list.append(example_prompt)

    return "".join(prompt_list)



def generate_pddl(system_prompt:str, problem_description:str):
    user_content = f"actual description: {problem_description} \n\
                    output: <YOUR_OUTPUT> \n \
                    Output ONLY the PDDL problem. Do not include explanations, markdown, code blocks, comments. The response must begin with: '(define' and end with: ')'"
        
    response = client.responses.create(
        model="gpt-4o",
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
    )

    return response.output_text



def parse_logs(logs:str):
    error_logs = []
    logs_list = logs.split("\n")

    i = 0
    while (("INFO" in logs_list[i] or "Parsing" in logs_list[i]) and i < len(logs_list)): 
        i += 1
    
    while ("translate" not in logs_list[i] and i < len(logs_list)):
        error_logs.append(f"{logs_list[i]} ")
        i += 1
    
    return "".join(error_logs)



def classify_error(log:str):
    if "predicate" in log:
        return f"Predicate error - {log}"
    elif "object" in log:
        return f"Object error - {log}"
    return f"Unknown error - {log}"



def validate_pddl(pddl_filepath:str):
    cmd = [ "./downward/fast-downward.py",
           "--translate",
           "--alias lama-first",
            pddl_filepath,
        ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    exit_code = result.returncode
    
    if exit_code == 0 and "unsolvable" not in result.stdout: 
        return True, ""
    elif exit_code == 0:
        if "goal" in result.stdout:
            return False, f"validation error: Error in goal"
        return False, f"validation error: Error in initial state"
    
    error_log = parse_logs(result.stdout)
    error_type = classify_error(error_log)
    return False, f"translation error: {error_type} - {error_log}"



def generate_diagnosis(problem_description:str, system_prompt:str, invalid_pddls:list, error_logs:list):
    history = ""
    for i in range(len(error_logs) - 1):
        history += f"{i + 1}: {error_logs[i]} \n\ "

    user_content = f"The following PDDL is wrong. Explain the root cause of the error and describe how to fix it. There may be more than 1 error: \n \
                    actual description: {problem_description} \n\
                    pddl: {invalid_pddls[-1]} \n\
                    current error: {error_logs[-1]} \n\
                    previous errors: {history} \n \
                    Only output the diagnosis and how to solve it"
        
    response = client.responses.create(
                model="gpt-4o",
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ]
            )

    return response.output_text

def correct_pddl(problem_description:str, system_prompt:str, invalid_pddls:list, error_logs:list, diagnosis:str):
    user_content = f"The following PDDL is wrong. Carefully analyze the planner error and fix the PDDL accordingly: \n \
                    actual description: {problem_description} \n\
                    output: {invalid_pddls[-1]} \n\
                    current error: {error_logs[-1]} \n\
                    diagnosis: {diagnosis} \n \
                    Output ONLY the PDDL problem. Do not include explanations, markdown, code blocks, comments. The response must begin with: '(define' and end with: ')'"
        
    response = client.responses.create(
                model="gpt-4o",
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ]
            )

    return response.output_text



def generate_sas_plan(pddl_filepath:str):
    cmd = [ "./downward/fast-downward.py",
           "--alias lama-first",
            pddl_filepath,
        ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode



def verify_sas_plan(domain_filepath:str, pddl_filepath:str):
    cmd = [ "ecl",
           "--shell",
           "inval-main.lsp ",
            domain_filepath,
            pddl_filepath,
            "."
        ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode



if __name__ == "__main__":
    PROBLEM_TYPE = "blocksworld"
    domain_filepath, problem_filelist, pddl_filelist = generate_filepaths(problem_type=PROBLEM_TYPE, sample_count=2)
    system_prompt = generate_system_prompt(problem_type=PROBLEM_TYPE, domain_filepath=DOMAIN_FILEPATH, problem_filelist=PROBLEM_FILELIST, pddl_filelist=PDDL_FILELIST)
    
    #pipeline
    
    problem_description = ""
    for file in os.listdir(f"{PROBLEMS_DIR}/{PROBLEM_TYPE}"):
        if "sample" not in file:
            #loading in problem descriptions
            filepath = f"{PROBLEMS_DIR}/{PROBLEM_TYPE}/{file}"
            with open(filepath, "r") as f:
                problem_description = f.read()
    
            #generate pddl based on description
            pddl = generate_pddl(system_prompt=system_prompt, problem_description=problem_description)
            pddl_filepath = f"./PDDL/{PROBLEM_TYPE}/pb{i + 1}.pddl"
            with open(pddl_filepath, "w") as file:
                file.write(pddl)

            #validate pddl and correct it if there are errors
            isValid = False
            invalid_pddls, error_logs = []
            for i in range(3):
                isValid, error_log = validate_pddl(pddl_filepath=pddl_filepath)

                if not isValid: 
                    invalid_pddls.append(pddl)
                    error_logs.append(error_log)
                    diagnosis = generate_diagnosis(problem_description=problem_description, system_prompt=system_prompt, invalid_pddls=invalid_pddls, error_logs=error_logs)
                    pddl = correct_pddl(problem_description=problem_description, system_prompt=system_prompt, invalid_pddls=invalid_pddls, error_logs=error_logs, diagnosis=diagnosis)
                    with open(pddl_filepath, "w") as file:
                        file.write(pddl)

                else:
                    break
            
            if isValid:
                exit_code = generate_sas_plan(pddl_filepath=pddl_filepath)
                if exit_code == 0:
                    status_code = verify_sas_plan(domain_filepath=domain_filepath, pddl_filepath=pddl_filepath)
                    if status_code == 0:
                        print(f"{pddl_filepath} is a valid pddl file")


        
    
    
    
    
    