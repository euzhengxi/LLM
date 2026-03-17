import os
import logging
import subprocess

from openai import OpenAI
from dotenv import load_dotenv

logger = logging.getLogger()
logging.basicConfig(filename='pipeline_logs.txt', level=logging.INFO)

PROBLEMS_DIR = "/home/zx/LLM/neuro_symbolic/problems"
SAMPLE_COUNT = 2

def generate_filepaths(problem_type:str, sample_count:int):
    domain_filepath = f"PDDL/{problem_type}/domain.pddl"

    sample_problems, sample_pddls = [], []
    for i in range(sample_count):
        sample_problems.append(f"problems/{problem_type}/sample{i + 1}.txt")
        sample_pddls.append(f"PDDL/{problem_type}/sample{i + 1}.pddl")

    return domain_filepath, sample_problems, sample_pddls 



def generate_system_prompt(problem_type:str, domain_filepath:str, sample_problems:list, sample_pddls:list):
    #create template for system prompt - context + domain knowledge
    domain_pddl = ""
    with open(domain_filepath, "r") as file:
        domain_pddl = file.read()
    
    system_prompt = f"You are generating the initial and goal state for the {problem_type} problem for a classical solver based on a short description. \
                    This is the domain pddl: {domain_pddl} \n \
                    Ensure the output is in PDDL format.The following are a few examples: \n"
    
    prompt_list = [system_prompt]

    #complement template with a few examples for few shot prompting
    n = len(sample_problems)
    problem_description, pddl = "", ""
    for i in range(n):
        with open(sample_problems[i], "r") as f1:
            problem_description = f1.read()
        
        with open(sample_pddls[i], "r") as f2:
            pddl = f2.read()
        
        example_prompt = f"Example {i + 1}: \n\
                    - description: {problem_description} \n\
                    - output: {pddl} \n"
        
        if (i != n - 1):
            example_prompt += "\n"

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

    logs_list = logs.split("\n")
    i = 0
    while (("INFO" in logs_list[i] or "Parsing" in logs_list[i] or len(logs_list[i]) < 5) and i < len(logs_list)): 
        i += 1
    
    error_logs = []
    while ("translate" not in logs_list[i] and i < len(logs_list)):
        error_logs.append(f"{logs_list[i]} ")
        i += 1
    
    return "".join(error_logs)



def classify_error(log:str):
    if "predicate" in log:
        return "Predicate error"
    elif "object" in log:
        return "Object error"
    return "Unknown error"



def validate_pddl(domain_filepath:str, pddl_filepath:str):
    cmd = [ "downward/fast-downward.py",
            "--translate",
            domain_filepath,
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
        history += f"{i + 1}: {error_logs[i]} \n"

    user_content = f"The following PDDL is wrong. Explain the root cause of the error and describe how to fix it. \n \
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



def generate_sas_plan(domain_filepath:str, pddl_filepath:str, sas_filepath:str):
    cmd = [ "downward/fast-downward.py",
           "--alias", 
           "lama-first",
           "--plan-file",
            sas_filepath,
            domain_filepath,
            pddl_filepath,
        ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode



def verify_sas_plan(domain_filepath:str, pddl_filepath:str):
    cmd = [ "ecl",
           "--shell",
           "INVAL/inval-main.lsp",
            domain_filepath,
            pddl_filepath,
            "."
        ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode



if __name__ == "__main__":
    load_dotenv()
    OPENAI_API_KEY = os.getenv("OPENAI")
    client = OpenAI(api_key=OPENAI_API_KEY)

    problem_type = "blocksworld"
    domain_filepath, sample_problems, sample_pddls = generate_filepaths(problem_type=problem_type, sample_count=SAMPLE_COUNT)
    system_prompt = generate_system_prompt(problem_type=problem_type, domain_filepath=domain_filepath, sample_problems=sample_problems, sample_pddls=sample_pddls)
    
    #read problem statements
    problems = []
    for file in os.listdir(f"{PROBLEMS_DIR}/{problem_type}"):
        if "sample" not in file:
            #loading in problem descriptions
            filepath = f"{PROBLEMS_DIR}/{problem_type}/{file}"
            filename = file.split(".")[0]
            with open(filepath, "r") as f:
                problems.append((filename, f.read()))
    
    logger.info(f"Generating {len(problems)} problem pddls... \n")

    #pipeline
    for filename, problem_description in problems:
        #generate pddl based on description
        pddl = generate_pddl(system_prompt=system_prompt, problem_description=problem_description)
        pddl_filepath = f"PDDL/{problem_type}/{filename}.pddl"
        with open(pddl_filepath, "w") as f:
            f.write(pddl)

        logger.info(f">>> PDDL generated for {filename}")

        #validate pddl and correct it if there are errors
        isValid = False
        invalid_pddls, error_logs = [], []
        for j in range(3):
            isValid, error_log = validate_pddl(domain_filepath=domain_filepath, pddl_filepath=pddl_filepath)

            if not isValid: 
                invalid_pddls.append(pddl)
                error_logs.append(error_log)
                diagnosis = generate_diagnosis(problem_description=problem_description, system_prompt=system_prompt, invalid_pddls=invalid_pddls, error_logs=error_logs)
                logger.warning(f"Attempt {j + 1} at fixing pddl for {filename}: {error_log}")
                logger.warning(f"PDDL: {pddl}")
                logger.warning(f"{diagnosis} \n")
                pddl = correct_pddl(problem_description=problem_description, system_prompt=system_prompt, invalid_pddls=invalid_pddls, error_logs=error_logs, diagnosis=diagnosis)
                with open(pddl_filepath, "w") as f:
                    f.write(pddl)

            else:
                break
            
        if isValid:
            logger.info(f"Valid PDDL generated for {filename}")
            sas_filepath = f"sas/{problem_type}/sas_plan_{filename}"
            exit_code = generate_sas_plan(domain_filepath=domain_filepath, pddl_filepath=pddl_filepath, sas_filepath=sas_filepath)
            if exit_code == 0:
                logger.info(f"sas_plan generated for {filename}")
                status_code = verify_sas_plan(domain_filepath=domain_filepath, pddl_filepath=pddl_filepath)
                if status_code == 0:
                    logger.info(f"sas_plan for {filename} validated")
    
        logger.info("\n\n")

